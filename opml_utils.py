import os
import re
from xml.etree import ElementTree as ET
import xml.sax.saxutils as saxutils

def read_file_content(file_path):
    """Read file content with different encodings."""
    encodings = ['utf-8', 'latin-1', 'cp1252']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read(), encoding
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode file {file_path} with any of the attempted encodings")

def fix_xml_structure(content):
    """Fix the XML structure by finding and removing junk after the document element."""
    # Try to locate proper XML structure
    opml_match = re.search(r'<opml[^>]*>.*?</opml>', content, re.DOTALL)
    if opml_match:
        return opml_match.group(0)
    
    # If no complete OPML tag found, try building proper structure
    head_match = re.search(r'<head>.*?</head>', content, re.DOTALL)
    body_match = re.search(r'<body>.*?</body>', content, re.DOTALL)
    
    if head_match and body_match:
        return f'<?xml version="1.0" encoding="UTF-8"?>\n<opml version="2.0">\n{head_match.group(0)}\n{body_match.group(0)}\n</opml>'
    
    return content

def fix_common_xml_issues(content):
    """Fix common XML issues that might cause parsing errors."""
    # Replace unescaped ampersands not part of an entity
    content = re.sub(r'&(?!(amp|lt|gt|apos|quot|#\d+|#x[0-9a-fA-F]+);)', '&amp;', content)
    
    # Fix missing quotes around attribute values
    content = re.sub(r'=(\w+)(\s+|\>)', r'="\1"\2', content)
    
    # Fix self-closing tags
    content = re.sub(r'<([\w:]+)([^>]*)/>', r'<\1\2 />', content)
    
    # Remove invalid XML characters
    content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', content)
    
    # Ensure proper XML declaration
    if not content.strip().startswith('<?xml'):
        content = '<?xml version="1.0" encoding="UTF-8"?>\n' + content
    
    return content

def check_and_fix_opml(file_path):
    """Check if an OPML file is valid XML and fix common issues if not."""
    try:
        # Read file content with appropriate encoding
        content, encoding = read_file_content(file_path)
        
        # Try parsing the original content
        try:
            ET.fromstring(content)
            print(f"✓ {file_path} is valid XML")
            return True
        except Exception as e:
            original_error = str(e)
            print(f"✗ {file_path} has XML issues: {original_error}")
            
            # First, fix the XML structure (remove junk after document element)
            content = fix_xml_structure(content)
            
            # Then apply common XML fixes
            content = fix_common_xml_issues(content)
            
            # Try parsing the fixed content
            try:
                ET.fromstring(content)
                print(f"  ↳ Successfully fixed issues in {file_path}")
                
                # Backup the original file
                backup_path = file_path + ".bak"
                with open(backup_path, 'w', encoding=encoding) as f:
                    f.write(content)
                print(f"  ↳ Original file backed up to {backup_path}")
                
                # Save the fixed content
                with open(file_path, 'w', encoding=encoding) as f:
                    f.write(content)
                print(f"  ↳ Fixed content saved to {file_path}")
                return True
            except Exception as e:
                print(f"  ↳ Could not fix issues automatically: {str(e)}")
                
                # Manual examination of the file to help diagnose issues
                print(f"  ↳ Examining file structure...")
                with open(file_path, 'r', encoding=encoding) as f:
                    lines = f.readlines()
                    
                    # Check first few lines
                    if len(lines) > 0:
                        first_line = lines[0].strip()
                        print(f"  ↳ First line: {first_line[:60]}...")
                    
                    # Try to identify XML declaration and root element
                    xml_decl = None
                    root_start = None
                    for i, line in enumerate(lines[:10]):  # Check first 10 lines
                        if '<?xml' in line:
                            xml_decl = (i, line.strip())
                        if '<opml' in line:
                            root_start = (i, line.strip())
                    
                    if xml_decl:
                        print(f"  ↳ XML declaration found at line {xml_decl[0]+1}: {xml_decl[1]}")
                    else:
                        print("  ↳ No XML declaration found")
                        
                    if root_start:
                        print(f"  ↳ Root element starts at line {root_start[0]+1}: {root_start[1]}")
                    else:
                        print("  ↳ No root element found")
                
                # Try an alternative approach for severe cases
                try:
                    # Create minimal valid OPML structure
                    print("  ↳ Attempting to extract and rebuild OPML structure...")
                    
                    # Extract outline elements
                    outline_matches = re.findall(r'<outline[^>]*>.*?</outline>|<outline[^>]*?/>', content, re.DOTALL)
                    
                    if outline_matches:
                        new_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
                        new_content += '<opml version="2.0">\n'
                        new_content += '<head><title>Reconstructed OPML</title></head>\n'
                        new_content += '<body>\n'
                        
                        for match in outline_matches:
                            # Fix common issues in outline elements
                            fixed_match = re.sub(r'&(?!(amp|lt|gt|apos|quot|#\d+|#x[0-9a-fA-F]+);)', '&amp;', match)
                            new_content += fixed_match + '\n'
                        
                        new_content += '</body>\n</opml>'
                        
                        # Try parsing the reconstructed content
                        try:
                            ET.fromstring(new_content)
                            print(f"  ↳ Successfully reconstructed OPML for {file_path}")
                            
                            # Save the reconstructed content
                            reconstructed_path = file_path + ".reconstructed"
                            with open(reconstructed_path, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            print(f"  ↳ Reconstructed OPML saved to {reconstructed_path}")
                            
                            # Optionally replace the original
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            print(f"  ↳ Original file replaced with reconstructed OPML")
                            return True
                        except Exception as e:
                            print(f"  ↳ Reconstruction failed: {str(e)}")
                    else:
                        print("  ↳ Could not find outline elements for reconstruction")
                except Exception as e:
                    print(f"  ↳ Advanced repair attempt failed: {str(e)}")
                
                return False
            
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return False

def process_directory(directory):
    """Process all OPML files in a directory."""
    fixed_count = 0
    error_count = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.opml') and not file.endswith('.bak') and not file.endswith('.reconstructed'):
                file_path = os.path.join(root, file)
                if check_and_fix_opml(file_path):
                    fixed_count += 1
                else:
                    error_count += 1
    
    print(f"\nProcessing complete: {fixed_count} files fixed, {error_count} files with remaining issues")

def create_sample_opml(output_path):
    """Create a sample valid OPML file for reference."""
    sample_opml = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>Sample OPML File</title>
  </head>
  <body>
    <outline text="Tech News" title="Tech News">
      <outline type="rss" text="Wired" title="Wired" xmlUrl="https://www.wired.com/feed/rss" htmlUrl="https://www.wired.com"/>
      <outline type="rss" text="TechCrunch" title="TechCrunch" xmlUrl="https://techcrunch.com/feed/" htmlUrl="https://techcrunch.com"/>
      <outline type="rss" text="Ars Technica" title="Ars Technica" xmlUrl="https://arstechnica.com/feed/" htmlUrl="https://arstechnica.com"/>
    </outline>
    <outline text="News" title="News">
      <outline type="rss" text="BBC News" title="BBC News" xmlUrl="https://feeds.bbci.co.uk/news/rss.xml" htmlUrl="https://www.bbc.com/news"/>
      <outline type="rss" text="Reuters" title="Reuters" xmlUrl="https://feeds.reuters.com/reuters/topNews" htmlUrl="https://www.reuters.com"/>
    </outline>
  </body>
</opml>"""
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(sample_opml)
    print(f"Created sample valid OPML file at {output_path}")

if __name__ == "__main__":
    base_dir = "opml"  # Change this to your OPML directory
    
    # Create a sample valid OPML file for reference
    create_sample_opml(os.path.join(base_dir, "sample_valid.opml"))
    
    # Process countries directory
    countries_dir = os.path.join(base_dir, "countries_without_category")
    if os.path.exists(countries_dir):
        print(f"\nProcessing country OPML files in {countries_dir}...\n")
        process_directory(countries_dir)
    
    # Process interests directory
    interests_dir = os.path.join(base_dir, "interests_without_category")
    if os.path.exists(interests_dir):
        print(f"\nProcessing interest OPML files in {interests_dir}...\n")
        process_directory(interests_dir)