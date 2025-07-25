#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Document converter module for RAG Document Indexer
Automatically converts .doc files to .docx format for proper processing
NEW: Backup files in parent directory with preserved folder structure
FIXED: Delete original .doc files after successful backup and conversion
"""

import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import tempfile


class DocumentConverter:
    """Converter for .doc files to .docx format with enhanced backup system and original deletion"""
    
    def __init__(self, backup_originals=True, delete_originals=False, config=None):
        """
        Initialize document converter
        
        Args:
            backup_originals: Whether to backup original .doc files
            delete_originals: Whether to delete .doc files after conversion (deprecated - always delete after backup)
            config: Configuration object with backup settings
        """
        self.backup_originals = backup_originals
        self.delete_originals = delete_originals  # Keep for compatibility but ignore
        self.config = config
        
        # Determine backup directory
        if config:
            self.backup_base_dir = config.get_backup_directory()
            self.documents_dir = config.DOCUMENTS_DIR
        else:
            # Fallback if no config provided
            self.backup_base_dir = "./doc_backups"
            self.documents_dir = None
        
        self.conversion_stats = {
            'attempted': 0,
            'successful': 0,
            'failed': 0,
            'failed_files': [],
            'backup_created': 0,
            'backup_failed': 0,
            'originals_deleted': 0,  # NEW: Track deleted original files
            'deletion_failed': 0     # NEW: Track failed deletions
        }
        
        # Check if conversion tools are available
        self.libreoffice_available = self._check_libreoffice()
        self.pandoc_available = self._check_pandoc()
        
        if not self.libreoffice_available and not self.pandoc_available:
            print("WARNING: No document conversion tools found!")
            print("Install LibreOffice: sudo apt-get install libreoffice")
            print("Or install pandoc: sudo apt-get install pandoc")
    
    def _check_libreoffice(self):
        """Check if LibreOffice is available"""
        try:
            result = subprocess.run(['libreoffice', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def _check_pandoc(self):
        """Check if pandoc is available"""
        try:
            result = subprocess.run(['pandoc', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def _backup_original_file(self, doc_path):
        """
        Create backup of original .doc file in parent directory with preserved structure
        
        Args:
            doc_path: Path to original .doc file
        
        Returns:
            str: Path to backup file if successful, None otherwise
        """
        if not self.backup_originals:
            return None
        
        try:
            doc_path = Path(doc_path)
            
            # Calculate relative path from documents directory
            if self.documents_dir:
                documents_path = Path(self.documents_dir).resolve()
                doc_path_resolved = doc_path.resolve()
                
                try:
                    # Get relative path from documents directory to the file
                    relative_path = doc_path_resolved.relative_to(documents_path)
                except ValueError:
                    # File is not within documents directory, use filename only
                    relative_path = doc_path.name
                    print(f"   WARNING: File {doc_path} is outside documents directory, using filename only for backup")
            else:
                # Fallback: use just the filename
                relative_path = doc_path.name
            
            # Create backup path preserving directory structure
            backup_base = Path(self.backup_base_dir)
            backup_file_path = backup_base / relative_path
            
            # Ensure backup directory exists
            backup_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Add timestamp to avoid conflicts if needed
            if backup_file_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                stem = backup_file_path.stem
                suffix = backup_file_path.suffix
                backup_file_path = backup_file_path.parent / f"{stem}_backup_{timestamp}{suffix}"
            
            # Copy the file preserving metadata
            shutil.copy2(doc_path, backup_file_path)
            
            print(f"   Ì†ΩÌ≥Å Backup created: {backup_file_path}")
            self.conversion_stats['backup_created'] += 1
            
            return str(backup_file_path)
            
        except Exception as e:
            print(f"   ‚ö†Ô∏è WARNING: Could not backup {doc_path}: {e}")
            self.conversion_stats['backup_failed'] += 1
            return None
    
    def _delete_original_file(self, doc_path):
        """
        Delete original .doc file after successful backup and conversion
        
        Args:
            doc_path: Path to original .doc file to delete
        
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            doc_path_obj = Path(doc_path)
            
            if doc_path_obj.exists():
                doc_path_obj.unlink()  # Delete the file
                print(f"   Ì†ΩÌ∑ëÔ∏è Original deleted: {doc_path_obj.name}")
                self.conversion_stats['originals_deleted'] += 1
                return True
            else:
                print(f"   ‚ö†Ô∏è WARNING: Original file not found for deletion: {doc_path}")
                return False
                
        except Exception as e:
            print(f"   ‚ùå ERROR: Could not delete original {doc_path}: {e}")
            self.conversion_stats['deletion_failed'] += 1
            return False
    
    def _convert_with_libreoffice(self, doc_path, output_dir):
        """
        Convert .doc to .docx using LibreOffice
        
        Args:
            doc_path: Path to .doc file
            output_dir: Output directory for .docx file
        
        Returns:
            tuple: (success, docx_path, error_message)
        """
        try:
            cmd = [
                'libreoffice',
                '--headless',
                '--convert-to', 'docx',
                '--outdir', str(output_dir),
                str(doc_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Find the converted file
                doc_name = Path(doc_path).stem
                docx_path = Path(output_dir) / f"{doc_name}.docx"
                
                if docx_path.exists():
                    return True, docx_path, None
                else:
                    return False, None, "Converted file not found"
            else:
                return False, None, result.stderr or "LibreOffice conversion failed"
                
        except subprocess.TimeoutExpired:
            return False, None, "LibreOffice conversion timed out"
        except Exception as e:
            return False, None, f"LibreOffice error: {str(e)}"
    
    def _convert_with_pandoc(self, doc_path, output_path):
        """
        Convert .doc to .docx using pandoc
        
        Args:
            doc_path: Path to .doc file
            output_path: Path for output .docx file
        
        Returns:
            tuple: (success, docx_path, error_message)
        """
        try:
            cmd = ['pandoc', str(doc_path), '-o', str(output_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and Path(output_path).exists():
                return True, output_path, None
            else:
                return False, None, result.stderr or "Pandoc conversion failed"
                
        except subprocess.TimeoutExpired:
            return False, None, "Pandoc conversion timed out"
        except Exception as e:
            return False, None, f"Pandoc error: {str(e)}"
    
    def convert_single_file(self, doc_path, target_dir=None):
        """
        Convert a single .doc file to .docx with enhanced backup and DELETION of original
        
        Args:
            doc_path: Path to .doc file to convert
            target_dir: Directory to save .docx file (default: same as source)
        
        Returns:
            tuple: (success, docx_path, error_message)
        """
        doc_path = Path(doc_path)
        
        if not doc_path.exists():
            return False, None, f"File not found: {doc_path}"
        
        if doc_path.suffix.lower() != '.doc':
            return False, None, f"Not a .doc file: {doc_path}"
        
        # Determine target directory
        if target_dir is None:
            target_dir = doc_path.parent
        else:
            target_dir = Path(target_dir)
            target_dir.mkdir(parents=True, exist_ok=True)
        
        # Target .docx file path
        docx_path = target_dir / f"{doc_path.stem}.docx"
        
        # Check if .docx already exists
        if docx_path.exists():
            print(f"   ‚ÑπÔ∏è INFO: {docx_path.name} already exists, skipping conversion")
            return True, docx_path, "Already exists"
        
        self.conversion_stats['attempted'] += 1
        
        # Step 1: Create backup BEFORE conversion
        backup_path = self._backup_original_file(doc_path)
        
        # Step 2: Try conversion with LibreOffice first
        success = False
        error_msg = None
        
        if self.libreoffice_available:
            print(f"   Ì†ΩÌ¥Ñ Converting {doc_path.name} with LibreOffice...")
            success, result_path, error_msg = self._convert_with_libreoffice(doc_path, target_dir)
            
            if success:
                docx_path = result_path
        
        # Fallback to pandoc if LibreOffice failed
        if not success and self.pandoc_available:
            print(f"   Ì†ΩÌ¥Ñ Retrying {doc_path.name} with pandoc...")
            success, result_path, error_msg = self._convert_with_pandoc(doc_path, docx_path)
            
            if success:
                docx_path = result_path
        
        # Step 3: Handle results
        if success:
            self.conversion_stats['successful'] += 1
            print(f"   ‚úÖ SUCCESS: Converted {doc_path.name} ‚Üí {docx_path.name}")
            
            if backup_path:
                print(f"   Ì†ΩÌ≥Å Original backed up to: {Path(backup_path).name}")
            
            # Step 4: FIXED - Always delete original after successful backup and conversion
            if backup_path:  # Only delete if backup was created successfully
                deletion_success = self._delete_original_file(doc_path)
                if deletion_success:
                    print(f"   ‚úÖ Workflow complete: backup ‚Üí convert ‚Üí delete original")
                else:
                    print(f"   ‚ö†Ô∏è WARNING: Conversion successful but could not delete original")
            else:
                print(f"   ‚ö†Ô∏è WARNING: No backup created, keeping original file")
            
            return True, docx_path, None
        else:
            self.conversion_stats['failed'] += 1
            self.conversion_stats['failed_files'].append(str(doc_path))
            print(f"   ‚ùå ERROR: Failed to convert {doc_path.name}: {error_msg}")
            
            # If backup was created but conversion failed, note it
            if backup_path:
                print(f"   Ì†ΩÌ≥Å Original preserved in backup: {Path(backup_path).name}")
            
            return False, None, error_msg
    
    def scan_and_convert_directory(self, directory_path, recursive=True):
        """
        Scan directory for .doc files and convert them to .docx with enhanced backup and deletion
        
        Args:
            directory_path: Directory to scan
            recursive: Whether to scan subdirectories
        
        Returns:
            dict: Conversion results with backup and deletion information
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            return {'error': f"Directory not found: {directory_path}"}
        
        print(f"Ì†ΩÌ≥Å Scanning for .doc files in: {directory_path}")
        if self.backup_originals:
            print(f"Ì†ΩÌ≥Å Backup directory: {self.backup_base_dir}")
        print(f"Ì†ΩÌ∑ëÔ∏è Original .doc files will be deleted after successful backup and conversion")
        
        # Find all .doc files
        if recursive:
            doc_files = list(directory_path.rglob("*.doc"))
        else:
            doc_files = list(directory_path.glob("*.doc"))
        
        if not doc_files:
            print("‚ÑπÔ∏è INFO: No .doc files found")
            return {
                'attempted': 0,
                'successful': 0,
                'failed': 0,
                'failed_files': [],
                'backup_created': 0,
                'backup_failed': 0,
                'originals_deleted': 0,
                'deletion_failed': 0,
                'message': 'No .doc files found'
            }
        
        print(f"Ì†ΩÌ≥Ñ Found {len(doc_files)} .doc files to convert")
        
        # Convert each file
        converted_files = []
        for doc_file in doc_files:
            success, docx_path, error = self.convert_single_file(doc_file)
            if success:
                converted_files.append(str(docx_path))
        
        # Return enhanced results with deletion statistics
        return {
            'attempted': self.conversion_stats['attempted'],
            'successful': self.conversion_stats['successful'],
            'failed': self.conversion_stats['failed'],
            'failed_files': self.conversion_stats['failed_files'],
            'converted_files': converted_files,
            'backup_created': self.conversion_stats['backup_created'],
            'backup_failed': self.conversion_stats['backup_failed'],
            'originals_deleted': self.conversion_stats['originals_deleted'],  # NEW
            'deletion_failed': self.conversion_stats['deletion_failed'],      # NEW
            'backup_directory': self.backup_base_dir,
            'success_rate': (self.conversion_stats['successful'] / self.conversion_stats['attempted'] * 100) if self.conversion_stats['attempted'] > 0 else 0
        }
    
    def print_conversion_summary(self):
        """Print enhanced summary of conversion operations including deletion statistics"""
        print(f"\nÌ†ΩÌ≥Ñ Document Conversion Summary:")
        print("=" * 50)
        print(f"Ì†ΩÌ≥Å Backup directory: {self.backup_base_dir}")
        print(f"Ì†ΩÌ≥ä Files attempted: {self.conversion_stats['attempted']}")
        print(f"‚úÖ Successfully converted: {self.conversion_stats['successful']}")
        print(f"‚ùå Failed conversions: {self.conversion_stats['failed']}")
        print(f"Ì†ΩÌ≥Å Backups created: {self.conversion_stats['backup_created']}")
        print(f"‚ö†Ô∏è Backup failures: {self.conversion_stats['backup_failed']}")
        print(f"Ì†ΩÌ∑ëÔ∏è Originals deleted: {self.conversion_stats['originals_deleted']}")  # NEW
        print(f"‚ùå Deletion failures: {self.conversion_stats['deletion_failed']}")   # NEW
        
        if self.conversion_stats['attempted'] > 0:
            success_rate = (self.conversion_stats['successful'] / self.conversion_stats['attempted']) * 100
            print(f"Ì†ΩÌ≥à Success rate: {success_rate:.1f}%")
        
        if self.conversion_stats['failed_files']:
            print(f"\n‚ùå Failed files:")
            for failed_file in self.conversion_stats['failed_files']:
                print(f"   - {failed_file}")
        
        if self.conversion_stats['backup_created'] > 0:
            print(f"\nÌ†ΩÌ≥Å Original files backed up to: {self.backup_base_dir}")
            print(f"   Backup structure preserves original directory hierarchy")
        
        if self.conversion_stats['originals_deleted'] > 0:  # NEW
            print(f"\nÌ†ΩÌ∑ëÔ∏è Cleanup completed:")
            print(f"   Original .doc files deleted: {self.conversion_stats['originals_deleted']}")
            print(f"   Working directory now contains only .docx files")
            
        if self.conversion_stats['deletion_failed'] > 0:  # NEW
            print(f"   ‚ö†Ô∏è Deletion failures: {self.conversion_stats['deletion_failed']}")
            print(f"   Some original .doc files may still exist in working directory")
        
        print("=" * 50)
    
    def get_backup_info(self):
        """
        Get information about backup and deletion operations
        
        Returns:
            dict: Backup and deletion information
        """
        return {
            'backup_directory': self.backup_base_dir,
            'backup_enabled': self.backup_originals,
            'backups_created': self.conversion_stats['backup_created'],
            'backup_failures': self.conversion_stats['backup_failed'],
            'delete_originals': True,  # Always true now
            'originals_deleted': self.conversion_stats['originals_deleted'],  # NEW
            'deletion_failures': self.conversion_stats['deletion_failed']     # NEW
        }


def convert_doc_files_in_directory(directory_path, recursive=True, backup_originals=True, delete_originals=False, config=None):
    """
    Convenience function to convert all .doc files in a directory with enhanced backup and deletion
    
    Args:
        directory_path: Directory to scan and convert
        recursive: Whether to scan subdirectories
        backup_originals: Whether to backup original files
        delete_originals: Whether to delete original files after conversion (deprecated - always delete after backup)
        config: Configuration object with backup settings
    
    Returns:
        dict: Conversion results with backup and deletion information
    """
    converter = DocumentConverter(
        backup_originals=backup_originals,
        delete_originals=delete_originals,  # Ignored - always delete after backup
        config=config
    )
    
    results = converter.scan_and_convert_directory(directory_path, recursive)
    converter.print_conversion_summary()
    
    return results


def check_conversion_tools():
    """
    Check which document conversion tools are available
    
    Returns:
        dict: Available tools information
    """
    converter = DocumentConverter()
    
    tools_info = {
        'libreoffice_available': converter.libreoffice_available,
        'pandoc_available': converter.pandoc_available,
        'any_tool_available': converter.libreoffice_available or converter.pandoc_available
    }
    
    print("Ì†ΩÌ≥ä Document Conversion Tools Status:")
    print("=" * 50)
    print(f"LibreOffice: {'‚úÖ Available' if tools_info['libreoffice_available'] else '‚ùå Not available'}")
    print(f"Pandoc: {'‚úÖ Available' if tools_info['pandoc_available'] else '‚ùå Not available'}")
    
    if not tools_info['any_tool_available']:
        print("\n‚ö†Ô∏è WARNING: No conversion tools available!")
        print("Install with:")
        print("   sudo apt-get install libreoffice")
        print("   sudo apt-get install pandoc")
    else:
        print("\n‚úÖ Document conversion ready!")
        print("Ì†ΩÌ∑ëÔ∏è Original .doc files will be deleted after successful backup and conversion")
    
    print("=" * 50)
    
    return tools_info


def get_backup_directory_info(config):
    """
    Get information about backup directory setup
    
    Args:
        config: Configuration object
    
    Returns:
        dict: Backup directory information
    """
    if not config:
        return {'error': 'No configuration provided'}
    
    backup_dir = config.get_backup_directory()
    documents_dir = config.DOCUMENTS_DIR
    
    info = {
        'documents_directory': documents_dir,
        'backup_directory': backup_dir,
        'backup_exists': os.path.exists(backup_dir),
        'backup_writable': os.access(os.path.dirname(backup_dir), os.W_OK),
        'relative_structure': 'Preserves original directory structure',
        'delete_originals_after_backup': True  # NEW: Always true now
    }
    
    return info


if __name__ == "__main__":
    # Example usage
    print("Ì†ΩÌ≥ä Document Converter Test")
    check_conversion_tools()
    
    # Test conversion in current directory
    # results = convert_doc_files_in_directory("./data", recursive=True)
    # print(f"Conversion completed: {results}")