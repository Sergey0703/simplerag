#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File utilities module for RAG Document Indexer
Handles safe file reading with encoding detection, error handling, and automatic .doc conversion
NEW: Integrated with enhanced backup system and blacklist directory filtering
FIXED: Updated reporting to show original file deletion after conversion
"""

import os
from pathlib import Path
from llama_index.core import SimpleDirectoryReader, Document
from doc_converter import DocumentConverter, check_conversion_tools
from file_utils_core import (
    clean_content_from_null_bytes, 
    safe_read_file, 
    scan_files_in_directory,
    scan_directory_with_stats,
    print_directory_scan_summary
)


def scan_files_in_directory_filtered(directory, recursive=True, config=None, verbose=False):
    """
    Scan directory with blacklist filtering using config
    
    Args:
        directory: Directory to scan
        recursive: Whether to scan recursively
        config: Configuration object with blacklist settings
        verbose: Whether to print detailed info
    
    Returns:
        list: List of file paths (excludes blacklisted directories)
    """
    blacklist_directories = None
    if config:
        blacklist_directories = config.BLACKLIST_DIRECTORIES
    
    return scan_files_in_directory(directory, recursive, blacklist_directories, verbose)


def get_directory_stats_with_blacklist(directory, recursive=True, config=None, verbose=False):
    """
    Get directory statistics with blacklist filtering
    
    Args:
        directory: Directory to analyze
        recursive: Whether to scan recursively
        config: Configuration object with blacklist settings
        verbose: Whether to print detailed info
    
    Returns:
        dict: Directory statistics including blacklist info
    """
    blacklist_directories = None
    if config:
        blacklist_directories = config.BLACKLIST_DIRECTORIES
    
    return scan_directory_with_stats(directory, recursive, blacklist_directories, verbose)


def normalize_file_path(file_path):
    """
    Normalize file path for comparison
    
    Args:
        file_path: File path to normalize
    
    Returns:
        str: Normalized file path
    """
    return os.path.normpath(os.path.abspath(file_path))


def validate_file_path(file_path):
    """
    Validate if file path exists and is readable
    
    Args:
        file_path: Path to validate
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        if not os.path.isfile(file_path):
            return False, "Path is not a file"
        
        if not os.access(file_path, os.R_OK):
            return False, "File is not readable"
        
        return True, None
        
    except Exception as e:
        return False, f"Error accessing file: {e}"


def get_file_info(file_path):
    """
    Get detailed information about a file
    
    Args:
        file_path: Path to the file
    
    Returns:
        dict: File information including size, extension, etc.
    """
    try:
        path_obj = Path(file_path)
        stat_info = os.stat(file_path)
        
        return {
            'name': path_obj.name,
            'stem': path_obj.stem,
            'suffix': path_obj.suffix.lower(),
            'size': stat_info.st_size,
            'size_mb': stat_info.st_size / (1024 * 1024),
            'modified': stat_info.st_mtime,
            'is_text_file': path_obj.suffix.lower() in ['.txt', '.md', '.rst', '.log'],
            'is_document': path_obj.suffix.lower() in ['.pdf', '.docx', '.doc', '.rtf'],
            'is_image': path_obj.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
        }
    except Exception as e:
        return {'error': str(e)}


def scan_directory_files(directory, recursive=True, config=None):
    """
    Scan directory and return file statistics with blacklist filtering
    
    Args:
        directory: Directory to scan
        recursive: Whether to scan recursively
        config: Configuration object with blacklist settings
    
    Returns:
        dict: Directory statistics
    """
    return get_directory_stats_with_blacklist(directory, recursive, config, verbose=False)


class SimpleDirectoryLoader:
    """
    Enhanced directory loader with automatic .doc to .docx conversion and blacklist filtering
    FIXED: Updated to handle original file deletion after conversion
    """
    
    def __init__(self, input_dir, recursive=True, auto_convert_doc=True, backup_originals=True, config=None):
        """
        Initialize with directory path, conversion options, and config
        
        Args:
            input_dir: Input directory path
            recursive: Whether to scan recursively
            auto_convert_doc: Whether to automatically convert .doc files
            backup_originals: Whether to create backup copies
            config: Configuration object with enhanced settings
        """
        self.input_dir = input_dir
        self.recursive = recursive
        self.auto_convert_doc = auto_convert_doc
        self.backup_originals = backup_originals
        self.config = config
        self.documents_loaded = 0
        self.loading_time = 0
        self.conversion_results = None
        
        # Get blacklist from config
        self.blacklist_directories = []
        if config:
            self.blacklist_directories = config.BLACKLIST_DIRECTORIES
    
    def _preprocess_doc_files(self):
        """
        Preprocess .doc files by converting them to .docx with enhanced backup system
        FIXED: Original files are now deleted after successful backup and conversion
        
        Returns:
            dict: Conversion results with backup and deletion information
        """
        if not self.auto_convert_doc:
            return {'skipped': True, 'reason': 'Auto-conversion disabled'}
        
        print("Checking for .doc files that need conversion...")
        
        # Check if conversion tools are available
        try:
            tools_info = check_conversion_tools()
        except Exception as e:
            print(f"‚ö†Ô∏è Warning: Could not check conversion tools: {e}")
            return {'skipped': True, 'reason': 'Tool check failed'}
        
        if not tools_info['any_tool_available']:
            print("‚ö†Ô∏è WARNING: No .doc conversion tools available!")
            print("   Install LibreOffice: sudo apt-get install libreoffice")
            print("   Install pandoc: sudo apt-get install pandoc")
            print("   .doc files will be processed with binary fallback (may produce poor results)")
            return {'skipped': True, 'reason': 'No conversion tools'}
        
        # Find .doc files with blacklist filtering
        print("Ì†ΩÌ≥Å Scanning for .doc files...")
        if self.blacklist_directories:
            print(f"Ì†ΩÌ∫´ Excluding directories: {', '.join(self.blacklist_directories)}")
        
        all_files = scan_files_in_directory_filtered(
            self.input_dir, 
            self.recursive, 
            self.config, 
            verbose=True
        )
        
        # Filter for .doc files only
        doc_files = [f for f in all_files if f.lower().endswith('.doc')]
        
        if not doc_files:
            print("‚úÖ No .doc files found - no conversion needed")
            return {'converted': 0, 'message': 'No .doc files found'}
        
        print(f"Ì†ΩÌ≥Ñ Found {len(doc_files)} .doc files to convert")
        
        # Show backup directory info
        if self.backup_originals and self.config:
            backup_dir = self.config.get_backup_directory()
            print(f"Ì†ΩÌ≥Å Backup directory: {backup_dir}")
            print(f"Ì†ΩÌ≥Å Backup preserves original directory structure")
            print(f"Ì†ΩÌ∑ëÔ∏è Original .doc files will be deleted after successful backup and conversion")
        
        # Convert files with enhanced backup and deletion
        try:
            converter = DocumentConverter(
                backup_originals=self.backup_originals,
                delete_originals=False,  # Parameter ignored - always delete after backup
                config=self.config  # Pass config for backup directory
            )
            
            conversion_results = converter.scan_and_convert_directory(
                self.input_dir, 
                recursive=self.recursive
            )
            
            # Print enhanced results with deletion info
            if conversion_results['successful'] > 0:
                print(f"‚úÖ Successfully converted {conversion_results['successful']} .doc files to .docx")
                if conversion_results['backup_created'] > 0:
                    print(f"Ì†ΩÌ≥Å Created {conversion_results['backup_created']} backup files")
                # FIXED: Show deletion results
                if conversion_results['originals_deleted'] > 0:
                    print(f"Ì†ΩÌ∑ëÔ∏è Deleted {conversion_results['originals_deleted']} original .doc files from working directory")
                    print(f"‚úÖ Working directory now contains only .docx files for processing")
            
            if conversion_results['failed'] > 0:
                print(f"‚ùå Failed to convert {conversion_results['failed']} .doc files")
                print("   These files will use binary fallback processing")
            
            if conversion_results['backup_failed'] > 0:
                print(f"‚ö†Ô∏è Warning: {conversion_results['backup_failed']} backup operations failed")
            
            # FIXED: Show deletion failure warnings
            if conversion_results['deletion_failed'] > 0:
                print(f"‚ö†Ô∏è Warning: {conversion_results['deletion_failed']} original files could not be deleted")
                print(f"   Manual cleanup may be required in working directory")
            
            return conversion_results
            
        except Exception as e:
            print(f"‚ùå Error during .doc conversion: {e}")
            return {
                'error': str(e), 
                'attempted': len(doc_files), 
                'successful': 0, 
                'failed': len(doc_files),
                'backup_created': 0,
                'backup_failed': 0,
                'originals_deleted': 0,  # FIXED: Include deletion stats in error case
                'deletion_failed': 0
            }
    
    def load_data(self):
        """
        Load data using standard SimpleDirectoryReader with .doc conversion and blacklist filtering
        FIXED: Updated to handle original file deletion
        
        Returns:
            tuple: (documents, loading_stats, conversion_results)
        """
        print("Ì†ΩÌ≥Å Loading documents with automatic .doc conversion and blacklist filtering...")
        
        # Print directory analysis first
        if self.config:
            print("\nÌ†ΩÌ≥ä Analyzing directory structure...")
            stats = get_directory_stats_with_blacklist(
                self.input_dir, 
                self.recursive, 
                self.config, 
                verbose=True
            )
            print_directory_scan_summary(stats, show_blacklist_info=True)
        
        # Step 1: Convert .doc files to .docx with enhanced backup and deletion
        self.conversion_results = self._preprocess_doc_files()
        
        # Step 2: Load documents normally (now including converted .docx files)
        print("\nÌ†ΩÌ≥ñ Loading documents with SimpleDirectoryReader...")
        
        # Use standard SimpleDirectoryReader
        reader = SimpleDirectoryReader(
            input_dir=self.input_dir,
            recursive=self.recursive
        )
        
        import time
        start_time = time.time()
        
        try:
            documents = reader.load_data()
            self.documents_loaded = len(documents)
            print(f"‚úÖ Successfully loaded {self.documents_loaded} documents")
        except Exception as e:
            print(f"‚ùå Error during document loading: {e}")
            documents = []
            self.documents_loaded = 0
        
        self.loading_time = time.time() - start_time
        
        # Enhanced statistics with blacklist, backup and deletion info
        loading_stats = {
            'successful_files': self.documents_loaded,  # Approximate
            'failed_files': 0,  # Will be determined later from database comparison
            'encoding_issues': 0,  # Will be determined later
            'total_attempted': 0,  # Will be determined later from directory scan
            'failed_files_detailed': [],  # Will be filled later
            'conversion_results': self.conversion_results,
            'blacklist_applied': len(self.blacklist_directories) > 0,
            'blacklisted_directories': self.blacklist_directories,
            'directories_scanned': 0,  # Will be filled if stats available
            'directories_skipped': 0   # Will be filled if stats available
        }
        
        # Add directory scan stats if available
        if self.config:
            try:
                dir_stats = get_directory_stats_with_blacklist(
                    self.input_dir, 
                    self.recursive, 
                    self.config, 
                    verbose=False
                )
                loading_stats.update({
                    'directories_scanned': dir_stats['directories_scanned'],
                    'directories_skipped': dir_stats['directories_skipped'],
                    'total_files_found': dir_stats['total_files'],
                    'blacklisted_dirs_found': dir_stats['blacklisted_directories']
                })
            except Exception as e:
                print(f"‚ö†Ô∏è Could not get detailed directory stats: {e}")
        
        return documents, loading_stats, self.conversion_results
    
    def get_loading_stats(self):
        """
        Get enhanced loading statistics with blacklist and conversion info
        FIXED: Include deletion statistics
        
        Returns:
            dict: Enhanced loading statistics
        """
        return {
            'successful_files': self.documents_loaded,
            'failed_files': 0,  # To be determined later
            'encoding_issues': 0,  # To be determined later
            'total_attempted': 0,  # To be determined later
            'failed_files_detailed': [],
            'conversion_results': self.conversion_results,
            'blacklist_applied': len(self.blacklist_directories) > 0,
            'blacklisted_directories': self.blacklist_directories,
            'loading_time': self.loading_time
        }
    
    def get_failed_files_list(self):
        """
        Get failed files list (empty for now, will be determined later)
        
        Returns:
            list: Empty list (failed files will be determined later from database comparison)
        """
        return []
    
    def print_loading_summary(self):
        """
        Print comprehensive loading summary including conversion, blacklist and deletion results
        FIXED: Updated to show original file deletion information
        """
        print(f"\nÌ†ΩÌ≥ä Enhanced Document Loading Summary:")
        print(f"  Ì†ΩÌ≥ñ Documents loaded: {self.documents_loaded}")
        print(f"  ‚è±Ô∏è Loading time: {self.loading_time:.2f} seconds")
        
        # Blacklist information
        if self.blacklist_directories:
            print(f"\nÌ†ΩÌ∫´ Blacklist Filtering:")
            print(f"  Excluded directories: {', '.join(self.blacklist_directories)}")
            print(f"  This prevents processing files in backup/temp directories")
        else:
            print(f"\nÌ†ΩÌ∫´ Blacklist Filtering: Disabled (all directories scanned)")
        
        # Conversion information with deletion details
        if self.conversion_results and not self.conversion_results.get('skipped'):
            print(f"\nÌ†ΩÌ¥Ñ Document Conversion Summary:")
            print(f"  Ì†ΩÌ≥Ñ .doc files found: {self.conversion_results.get('attempted', 0)}")
            print(f"  ‚úÖ Successfully converted: {self.conversion_results.get('successful', 0)}")
            print(f"  ‚ùå Failed conversions: {self.conversion_results.get('failed', 0)}")
            print(f"  Ì†ΩÌ≥Å Backups created: {self.conversion_results.get('backup_created', 0)}")
            print(f"  ‚ö†Ô∏è Backup failures: {self.conversion_results.get('backup_failed', 0)}")
            
            # FIXED: Show deletion results
            print(f"  Ì†ΩÌ∑ëÔ∏è Original files deleted: {self.conversion_results.get('originals_deleted', 0)}")
            print(f"  ‚ùå Deletion failures: {self.conversion_results.get('deletion_failed', 0)}")
            
            if self.conversion_results.get('successful', 0) > 0:
                success_rate = (self.conversion_results['successful'] / self.conversion_results['attempted']) * 100
                print(f"  Ì†ΩÌ≥à Conversion success rate: {success_rate:.1f}%")
            
            if self.conversion_results.get('backup_directory'):
                print(f"  Ì†ΩÌ≥Å Backup location: {self.conversion_results['backup_directory']}")
                print(f"  Ì†ΩÌ≥Å Backup preserves original directory structure")
            
            # FIXED: Show cleanup status
            if self.conversion_results.get('originals_deleted', 0) > 0:
                print(f"  ‚úÖ Cleanup Status: Working directory contains only .docx files")
                print(f"     Original .doc files safely backed up and removed from processing")
            
            if self.conversion_results.get('deletion_failed', 0) > 0:
                print(f"  ‚ö†Ô∏è Cleanup Warning: {self.conversion_results['deletion_failed']} original files remain")
                print(f"     Manual cleanup may be needed in working directory")
            
            if self.conversion_results.get('failed_files'):
                print(f"  ‚ùå Failed files saved to conversion log")
        elif self.conversion_results and self.conversion_results.get('skipped'):
            reason = self.conversion_results.get('reason', 'Unknown')
            print(f"\nÌ†ΩÌ¥Ñ Document Conversion: Skipped ({reason})")
        
        print(f"  Ì†ΩÌ≥ä File-level success analysis will be performed after database operations")
    
    def get_conversion_summary(self):
        """
        Get detailed conversion summary including deletion information
        FIXED: Include deletion statistics
        
        Returns:
            dict: Conversion summary with all details including deletion info
        """
        if self.conversion_results:
            return {
                'conversion_attempted': not self.conversion_results.get('skipped', False),
                'doc_files_found': self.conversion_results.get('attempted', 0),
                'conversions_successful': self.conversion_results.get('successful', 0),
                'conversions_failed': self.conversion_results.get('failed', 0),
                'backups_created': self.conversion_results.get('backup_created', 0),
                'backup_failures': self.conversion_results.get('backup_failed', 0),
                'originals_deleted': self.conversion_results.get('originals_deleted', 0),  # FIXED: Added
                'deletion_failures': self.conversion_results.get('deletion_failed', 0),   # FIXED: Added
                'backup_directory': self.conversion_results.get('backup_directory'),
                'success_rate': self.conversion_results.get('success_rate', 0),
                'skip_reason': self.conversion_results.get('reason') if self.conversion_results.get('skipped') else None,
                'cleanup_completed': self.conversion_results.get('originals_deleted', 0) > 0,  # FIXED: Added
                'cleanup_needed': self.conversion_results.get('deletion_failed', 0) > 0     # FIXED: Added
            }
        else:
            return {
                'conversion_attempted': False,
                'skip_reason': 'No conversion results available'
            }


def create_safe_reader(documents_dir, recursive=True, auto_convert_doc=True, backup_originals=True, config=None):
    """
    Create a SimpleDirectoryLoader instance with .doc conversion and blacklist filtering
    FIXED: Updated to handle original file deletion
    
    Args:
        documents_dir: Directory to read from
        recursive: Whether to read recursively
        auto_convert_doc: Whether to automatically convert .doc files
        backup_originals: Whether to backup original .doc files
        config: Configuration object with enhanced settings
    
    Returns:
        SimpleDirectoryLoader: Enhanced loader instance with blacklist support and deletion handling
    """
    return SimpleDirectoryLoader(
        input_dir=documents_dir,
        recursive=recursive,
        auto_convert_doc=auto_convert_doc,
        backup_originals=backup_originals,
        config=config  # Pass config for blacklist and backup settings
    )


def check_directory_for_conversion_issues(documents_dir, config=None):
    """
    Check directory for potential conversion issues and conflicts
    FIXED: Updated to account for original file deletion
    
    Args:
        documents_dir: Directory to check
        config: Configuration object
    
    Returns:
        dict: Analysis of potential issues
    """
    issues = {
        'backup_conflicts': [],
        'blacklist_issues': [],
        'doc_files_in_blacklisted_dirs': [],
        'permissions_issues': [],
        'recommendations': []
    }
    
    try:
        # Check if backup directory would conflict with documents directory
        if config:
            backup_dir = config.get_backup_directory()
            documents_path = Path(documents_dir).resolve()
            backup_path = Path(backup_dir).resolve()
            
            # Check if backup directory is inside documents directory
            try:
                backup_path.relative_to(documents_path)
                issues['backup_conflicts'].append(f"Backup directory {backup_dir} is inside documents directory")
                issues['recommendations'].append("Move backup directory outside of documents directory")
            except ValueError:
                pass  # Good - backup is outside documents directory
            
            # Check blacklist directories
            blacklist_dirs = config.BLACKLIST_DIRECTORIES
            if backup_path.name not in blacklist_dirs:
                issues['blacklist_issues'].append(f"Backup directory name '{backup_path.name}' not in blacklist")
                issues['recommendations'].append(f"Add '{backup_path.name}' to BLACKLIST_DIRECTORIES")
        
        # Check for .doc files in directories that would be blacklisted
        if config and config.BLACKLIST_DIRECTORIES:
            all_files = scan_files_in_directory(documents_dir, recursive=True, blacklist_directories=None)
            doc_files = [f for f in all_files if f.lower().endswith('.doc')]
            
            for doc_file in doc_files:
                if config.is_blacklisted_directory(doc_file):
                    issues['doc_files_in_blacklisted_dirs'].append(doc_file)
            
            if issues['doc_files_in_blacklisted_dirs']:
                issues['recommendations'].append("Some .doc files are in blacklisted directories and won't be processed")
        
        # Check write permissions for backup directory
        if config:
            backup_dir = config.get_backup_directory()
            backup_parent = Path(backup_dir).parent
            if not os.access(backup_parent, os.W_OK):
                issues['permissions_issues'].append(f"No write permission for backup parent directory: {backup_parent}")
                issues['recommendations'].append(f"Ensure write permissions for {backup_parent}")
            
            # FIXED: Check write permissions for documents directory (needed for deletion)
            if not os.access(documents_dir, os.W_OK):
                issues['permissions_issues'].append(f"No write permission for documents directory: {documents_dir}")
                issues['recommendations'].append(f"Write permission needed for documents directory to delete original .doc files")
    
    except Exception as e:
        issues['permissions_issues'].append(f"Error checking directory: {str(e)}")
    
    return issues


def print_conversion_readiness_check(documents_dir, config=None):
    """
    Print a readiness check for document conversion
    FIXED: Updated to mention original file deletion
    
    Args:
        documents_dir: Directory to check
        config: Configuration object
    """
    print("\nÌ†ΩÌ≥ä DOCUMENT CONVERSION READINESS CHECK:")
    print("=" * 50)
    
    # Check conversion tools
    try:
        tools_info = check_conversion_tools()
        print(f"Ì†ΩÌ≥ä Conversion tools: {'‚úÖ Ready' if tools_info['any_tool_available'] else '‚ùå Missing'}")
    except Exception as e:
        print(f"Ì†ΩÌ≥ä Conversion tools: ‚ùå Error checking - {e}")
    
    # Check directory issues
    if config:
        issues = check_directory_for_conversion_issues(documents_dir, config)
        
        print(f"Ì†ΩÌ≥Å Backup directory: {config.get_backup_directory()}")
        print(f"Ì†ΩÌ∫´ Blacklist enabled: {'‚úÖ Yes' if config.BLACKLIST_DIRECTORIES else '‚ùå No'}")
        print(f"Ì†ΩÌ∑ëÔ∏è Original deletion: ‚úÖ Enabled (after successful backup and conversion)")
        
        if issues['backup_conflicts']:
            print(f"‚ö†Ô∏è Backup conflicts: {len(issues['backup_conflicts'])}")
            for conflict in issues['backup_conflicts']:
                print(f"   - {conflict}")
        
        if issues['doc_files_in_blacklisted_dirs']:
            print(f"‚ö†Ô∏è .doc files in blacklisted dirs: {len(issues['doc_files_in_blacklisted_dirs'])}")
        
        if issues['permissions_issues']:
            print(f"‚ö†Ô∏è Permission issues: {len(issues['permissions_issues'])}")
            for issue in issues['permissions_issues']:
                print(f"   - {issue}")
        
        if issues['recommendations']:
            print(f"\nÌ†ΩÌ≤° Recommendations:")
            for rec in issues['recommendations']:
                print(f"   - {rec}")
    else:
        print(f"‚ö†Ô∏è No configuration provided - using defaults")
    
    print("=" * 50)