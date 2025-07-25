#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Loading helpers module for RAG Document Indexer
Contains helper functions for document loading and processing
NEW: Fully integrated with enhanced backup system, blacklist filtering, and ENHANCED PDF PROCESSING
"""

import time
from datetime import datetime


def load_and_process_documents_enhanced(config, progress_tracker):
    """
    Enhanced document loading with automatic .doc conversion, blacklist filtering, PDF processing, and comprehensive features
    
    Args:
        config: Configuration object with enhanced settings
        progress_tracker: Progress tracker instance
    
    Returns:
        tuple: (text_documents, image_documents, processing_summary)
    """
    print(f"?? Loading documents from folder: {config.DOCUMENTS_DIR}")
    progress_tracker.add_checkpoint("Document loading started")
    
    # Print configuration summary
    print("\n?? Enhanced Loading Configuration:")
    print(f"   ?? Documents directory: {config.DOCUMENTS_DIR}")
    print(f"   ?? Backup directory: {config.get_backup_directory()}")
    print(f"   ?? Blacklisted directories: {', '.join(config.BLACKLIST_DIRECTORIES)}")
    print(f"   ?? Auto .doc conversion: {'?' if config.AUTO_CONVERT_DOC else '?'}")
    print(f"   ?? Backup originals: {'?' if config.BACKUP_ORIGINAL_DOC else '?'}")
    print(f"   ?? Enhanced PDF processing: {'?' if config.is_feature_enabled('enhanced_pdf_processing') else '?'}")
    
    # Enhanced document loading with automatic .doc conversion, blacklist filtering, and PDF processing
    print("\n?? Enhanced Document Loading with Auto .doc Conversion, PDF Processing & Blacklist Filtering...")
    
    # Import required modules
    from file_utils import create_safe_reader, print_conversion_readiness_check
    from ocr_processor import create_ocr_processor
    from directory_scanner import get_enhanced_directory_summary, print_enhanced_directory_summary
    
    # Perform readiness check
    print_conversion_readiness_check(config.DOCUMENTS_DIR, config)
    
    # NEW: Enhanced directory analysis with PDF support
    print("\n?? Performing enhanced directory analysis...")
    enhanced_summary = get_enhanced_directory_summary(
        config.DOCUMENTS_DIR, 
        recursive=True, 
        analyze_pdfs=config.is_feature_enabled('enhanced_pdf_processing')
    )
    
    # Print detailed directory summary
    print_enhanced_directory_summary(enhanced_summary)
    
    # Create enhanced reader with full config integration
    reader = create_safe_reader(
        config.DOCUMENTS_DIR, 
        recursive=True,
        auto_convert_doc=config.AUTO_CONVERT_DOC,      # From config
        backup_originals=config.BACKUP_ORIGINAL_DOC,   # From config
        config=config  # Pass full config for blacklist and backup settings
    )
    
    # Load documents (now with blacklist filtering, .doc conversion, and enhanced backup)
    text_documents, loading_stats, conversion_results = reader.load_data()
    
    # Print detailed loading summary including conversion, blacklist, and PDF results
    reader.print_loading_summary()
    
    progress_tracker.add_checkpoint("Text documents loaded", len(text_documents))
    
    # Load images with OCR if enabled
    image_documents = []
    ocr_stats = {}
    
    if config.ENABLE_OCR:
        print("\n?? Processing images with enhanced OCR...")
        ocr_processor = create_ocr_processor(
            quality_threshold=config.OCR_QUALITY_THRESHOLD,
            batch_size=config.OCR_BATCH_SIZE,
            config=config
        )
        
        # Process images with blacklist filtering
        image_docs, ocr_stats = ocr_processor.process_images_in_directory(config.DOCUMENTS_DIR)
        image_documents.extend(image_docs)
        
        progress_tracker.add_checkpoint("Images processed with OCR", len(image_documents))
    
    # Create comprehensive processing summary with PDF statistics
    processing_summary = {
        'documents_loaded': len(text_documents),
        'images_processed': len(image_documents),
        'conversion_results': conversion_results,
        'loading_stats': loading_stats,
        'ocr_stats': ocr_stats,
        'total_documents': len(text_documents) + len(image_documents),
        'blacklist_applied': loading_stats.get('blacklist_applied', False),
        'blacklisted_directories': loading_stats.get('blacklisted_directories', []),
        'directories_scanned': loading_stats.get('directories_scanned', 0),
        'directories_skipped': loading_stats.get('directories_skipped', 0),
        'backup_directory': config.get_backup_directory(),
        'enhanced_features_used': [],
        'directory_analysis': enhanced_summary,  # NEW: Include directory analysis
        'pdf_processing_summary': {}  # NEW: PDF processing summary
    }
    
    # Track which enhanced features were actually used
    enhanced_features_used = []
    
    if conversion_results and not conversion_results.get('skipped'):
        if conversion_results.get('successful', 0) > 0:
            enhanced_features_used.append('Document conversion (.doc ? .docx)')
        if conversion_results.get('backup_created', 0) > 0:
            enhanced_features_used.append('Structured backup system')
    
    if loading_stats.get('blacklist_applied', False):
        enhanced_features_used.append('Blacklist directory filtering')
    
    if ocr_stats and ocr_stats.get('successful', 0) > 0:
        enhanced_features_used.append('OCR text extraction')
    
    # NEW: Track PDF processing usage
    pdf_stats = {}
    if hasattr(reader, 'hybrid_processor') and hasattr(reader.hybrid_processor, 'pdf_processor'):
        pdf_processor = reader.hybrid_processor.pdf_processor
        if pdf_processor and pdf_processor.stats['files_processed'] > 0:
            enhanced_features_used.append('Enhanced PDF processing')
            pdf_stats = pdf_processor.get_processing_stats()
            
            # Add PDF processing summary
            processing_summary['pdf_processing_summary'] = {
                'files_processed': pdf_stats['files_processed'],
                'total_pages': pdf_stats['total_pages'],
                'text_extracted_chars': pdf_stats['text_extracted_chars'],
                'method_usage': pdf_stats['method_usage'],
                'average_chars_per_page': pdf_stats.get('average_chars_per_page', 0),
                'processing_speed': pdf_stats.get('average_processing_speed', 0)
            }
    
    # Add OCR rotation stats if available
    if 'ocr_processor' in locals() and hasattr(ocr_processor, 'get_processing_stats'):
        ocr_processing_stats = ocr_processor.get_processing_stats()
        processing_summary['rotation_stats'] = ocr_processing_stats.get('rotation_stats', {})
        
        if processing_summary['rotation_stats'].get('rotations_applied', 0) > 0:
            enhanced_features_used.append('Auto-rotation correction')
    
    processing_summary['enhanced_features_used'] = enhanced_features_used
    
    return text_documents, image_documents, processing_summary


def print_enhanced_loading_summary(text_documents, image_documents, loading_stats, loading_time):
    """
    Print comprehensive loading summary with enhanced metrics including blacklist, backup, and PDF info
    
    Args:
        text_documents: List of text documents
        image_documents: List of image documents  
        loading_stats: Loading statistics with blacklist, conversion, and PDF info
        loading_time: Time taken for loading
    """
    print(f"\n?? ENHANCED DOCUMENT LOADING RESULTS:")
    print(f"?? Loading time: {loading_time:.2f}s ({loading_time/60:.1f}m)")
    
    # Document counts
    total_docs = len(text_documents) + len(image_documents)
    print(f"?? Text documents: {len(text_documents)}")
    print(f"??? Image documents: {len(image_documents)}")
    print(f"?? Total documents: {total_docs}")
    
    # Enhanced blacklist information
    if loading_stats.get('blacklist_applied', False):
        print(f"\n?? Blacklist Filtering Results:")
        blacklisted_dirs = loading_stats.get('blacklisted_directories', [])
        print(f"   Excluded directories: {', '.join(blacklisted_dirs)}")
        print(f"   Directories scanned: {loading_stats.get('directories_scanned', 0):,}")
        print(f"   Directories skipped: {loading_stats.get('directories_skipped', 0):,}")
        
        if loading_stats.get('blacklisted_dirs_found'):
            found_dirs = loading_stats['blacklisted_dirs_found']
            if found_dirs:
                print(f"   Blacklisted dirs found: {', '.join(found_dirs[:3])}")
                if len(found_dirs) > 3:
                    print(f"   ... and {len(found_dirs) - 3} more")
        
        print(f"   ? This prevents processing files in backup/temp directories")
    else:
        print(f"\n?? Blacklist Filtering: Disabled (all directories processed)")
    
    # Enhanced conversion statistics
    if loading_stats.get('conversion_results'):
        conversion = loading_stats['conversion_results']
        if not conversion.get('skipped'):
            print(f"\n?? Document Conversion Results:")
            print(f"   ?? .doc files found: {conversion.get('attempted', 0)}")
            print(f"   ? Successfully converted: {conversion.get('successful', 0)}")
            print(f"   ? Failed conversions: {conversion.get('failed', 0)}")
            
            # Enhanced backup information
            print(f"   ?? Backup System:")
            print(f"     Backups created: {conversion.get('backup_created', 0)}")
            print(f"     Backup failures: {conversion.get('backup_failed', 0)}")
            
            if conversion.get('backup_directory'):
                print(f"     Backup location: {conversion['backup_directory']}")
                print(f"     Structure: Preserves original directory hierarchy")
            
            if conversion.get('successful', 0) > 0:
                success_rate = (conversion['successful'] / conversion['attempted']) * 100
                print(f"   ?? Conversion success rate: {success_rate:.1f}%")
                
                # Show impact
                print(f"   ? Impact: Converted files now accessible for advanced parsing")
        else:
            reason = conversion.get('reason', 'Unknown')
            print(f"\n?? Document Conversion: Skipped ({reason})")
    
    # NEW: Enhanced PDF processing statistics
    if loading_stats.get('pdf_processing_summary'):
        pdf_summary = loading_stats['pdf_processing_summary']
        print(f"\n?? ENHANCED PDF PROCESSING RESULTS:")
        print(f"   ?? PDF files processed: {pdf_summary.get('files_processed', 0)}")
        print(f"   ?? Total pages: {pdf_summary.get('total_pages', 0):,}")
        print(f"   ?? Text extracted: {pdf_summary.get('text_extracted_chars', 0):,} characters")
        
        if pdf_summary.get('average_chars_per_page', 0) > 0:
            print(f"   ?? Average chars per page: {pdf_summary['average_chars_per_page']:.0f}")
        
        if pdf_summary.get('processing_speed', 0) > 0:
            print(f"   ? Processing speed: {pdf_summary['processing_speed']:.1f} pages/sec")
        
        # Method usage for PDF
        method_usage = pdf_summary.get('method_usage', {})
        if method_usage:
            print(f"   ??? PDF Processing Methods Used:")
            for method, count in method_usage.items():
                if count > 0:
                    method_display = method.replace('_', ' ').title()
                    print(f"     - {method_display}: {count} files")
    
    # Directory analysis summary
    if loading_stats.get('directory_analysis'):
        dir_analysis = loading_stats['directory_analysis']
        if 'pdf_analysis' in dir_analysis and dir_analysis['pdf_analysis']:
            pdf_analysis = dir_analysis['pdf_analysis']
            print(f"\n?? PDF ANALYSIS INSIGHTS:")
            
            if 'pdf_types' in pdf_analysis:
                print(f"   ?? PDF Types Found:")
                for pdf_type, count in pdf_analysis['pdf_types'].items():
                    if count > 0:
                        print(f"     - {pdf_type.title()}: {count} files")
            
            if 'size_analysis' in pdf_analysis:
                size_info = pdf_analysis['size_analysis']
                if size_info.get('avg_pages_per_pdf', 0) > 0:
                    print(f"   ?? Average pages per PDF: {size_info['avg_pages_per_pdf']:.1f}")
                
                if size_info.get('large_pdfs'):
                    large_count = len(size_info['large_pdfs'])
                    print(f"   ?? Large PDFs (>50 pages): {large_count}")
            
            if 'processing_estimates' in pdf_analysis:
                estimates = pdf_analysis['processing_estimates']
                if estimates.get('estimated_total_time', 0) > 0:
                    total_time = estimates['estimated_total_time']
                    if total_time < 60:
                        print(f"   ?? Estimated PDF processing time: {total_time:.0f}s")
                    else:
                        print(f"   ?? Estimated PDF processing time: {total_time/60:.1f}m")
    
    # Advanced parsing statistics (if available)
    if 'file_breakdown' in loading_stats:
        breakdown = loading_stats['file_breakdown']
        print(f"\n?? File Type Breakdown:")
        print(f"   DOCX files: {breakdown.get('docx_files', 0)}")
        print(f"   DOC files: {breakdown.get('doc_files', 0)}")
        print(f"   PDF files: {breakdown.get('pdf_files', 0)}")  # NEW
        print(f"   Other files: {breakdown.get('other_files', 0)}")
    
    if 'processing_results' in loading_stats:
        results = loading_stats['processing_results']
        print(f"\n?? Processing Results:")
        print(f"   Documents created: {results.get('documents_created', 0)}")
        print(f"   Images extracted from docs: {results.get('images_extracted', 0)}")
        print(f"   Processing errors: {results.get('processing_errors', 0)}")
        print(f"   Success rate: {results.get('success_rate', 0):.1f}%")
    
    # Enhanced OCR statistics
    if 'ocr_stats' in loading_stats and loading_stats['ocr_stats']:
        ocr_stats = loading_stats['ocr_stats']
        print(f"\n?? OCR Processing Results:")
        print(f"   Images found: {ocr_stats.get('total_found', 0)}")
        print(f"   Successfully processed: {ocr_stats.get('successful', 0)}")
        print(f"   OCR success rate: {ocr_stats.get('success_rate', 0):.1f}%")
        print(f"   Total text extracted: {ocr_stats.get('total_text_length', 0)} characters")
        
        # Rotation statistics
        if 'rotation_stats' in ocr_stats:
            rotation_stats = ocr_stats['rotation_stats']
            if rotation_stats.get('images_tested', 0) > 0:
                print(f"   ?? Auto-Rotation Results:")
                print(f"     Images tested: {rotation_stats['images_tested']}")
                print(f"     Rotations applied: {rotation_stats['rotations_applied']}")
                print(f"     Quality improvements: {rotation_stats['improvements_found']}")
                if rotation_stats.get('timeouts', 0) > 0:
                    print(f"     Timeouts: {rotation_stats['timeouts']}")
        
        # Language detection
        if 'language_detection' in ocr_stats:
            lang_stats = ocr_stats['language_detection']
            if lang_stats:
                print(f"   ?? Language Detection:")
                for lang, count in lang_stats.items():
                    print(f"     {lang.capitalize()}: {count} images")
        
        # Quality failure analysis
        if 'quality_failures' in ocr_stats:
            quality_failures = ocr_stats['quality_failures']
            if quality_failures:
                print(f"   ?? Quality Failure Analysis:")
                for reason, count in quality_failures.items():
                    print(f"     {reason.replace('_', ' ').title()}: {count} images")
    
    # Method usage statistics
    if 'method_usage' in loading_stats:
        method_usage = loading_stats['method_usage']
        print(f"\n??? Processing Methods Used:")
        print(f"   Advanced parsing: {method_usage.get('advanced_parsing', 0)} files")
        print(f"   PDF processing: {method_usage.get('pdf_processing', 0)} files")  # NEW
        print(f"   Fallback processing: {method_usage.get('fallback_processing', 0)} files")
    
    # Enhanced features status
    if 'features_enabled' in loading_stats:
        features = loading_stats['features_enabled']
        print(f"\n? Enhanced Features Status:")
        feature_list = [
            ('Advanced parsing', features.get('advanced_parsing', False)),
            ('Image extraction', features.get('image_extraction', False)),
            ('Structure preservation', features.get('structure_preservation', False)),
            ('Table extraction', features.get('table_extraction', False)),
            ('Hybrid processing', features.get('hybrid_processing', False)),
            ('PDF processing', features.get('pdf_processing', False))  # NEW
        ]
        for feature_name, enabled in feature_list:
            status = "?" if enabled else "?"
            print(f"   {feature_name}: {status}")
    
    # Show enhanced features actually used
    if 'enhanced_features_used' in loading_stats:
        enhanced_features = loading_stats['enhanced_features_used']
        if enhanced_features:
            print(f"\n?? Enhanced Features Used:")
            for feature in enhanced_features:
                print(f"   ? {feature}")
        else:
            print(f"\n?? Enhanced Features Used: None (basic processing)")


def validate_documents_for_processing(documents, config):
    """
    Validate and filter documents for processing with enhanced reporting (including PDF validation)
    
    Args:
        documents: List of documents to validate
        config: Configuration object
    
    Returns:
        tuple: (documents_with_content, documents_without_content)
    """
    documents_with_content = []
    documents_without_content = []
    
    print("\n?? Validating documents for processing...")
    
    for doc in documents:
        file_name = doc.metadata.get('file_name', 'Unknown File')
        file_path = doc.metadata.get('file_path', file_name)
        file_type = doc.metadata.get('file_type', 'unknown')
        text_content = doc.text.strip()
        
        # Enhanced validation with more details including PDF-specific checks
        if not text_content:
            documents_without_content.append(f"{file_path} - EMPTY (no text extracted)")
        elif len(text_content) < config.MIN_CHUNK_LENGTH:
            # Special handling for PDF files - they might have different minimum requirements
            min_length = config.MIN_CHUNK_LENGTH
            if file_type == 'pdf':
                # Use PDF-specific minimum if available
                pdf_min_length = getattr(config, 'PDF_MIN_CONTENT_LENGTH', config.MIN_CHUNK_LENGTH)
                if len(text_content) >= pdf_min_length:
                    # Accept PDF with lower threshold
                    documents_with_content.append(doc)
                    continue
                min_length = pdf_min_length
            
            documents_without_content.append(f"{file_path} - TOO SHORT ({len(text_content)} chars, min: {min_length})")
        elif len(text_content.split()) < 3:
            documents_without_content.append(f"{file_path} - TOO FEW WORDS ({len(text_content.split())} words)")
        else:
            documents_with_content.append(doc)
    
    return documents_with_content, documents_without_content


def print_document_validation_summary(documents_with_content, documents_without_content):
    """
    Print enhanced summary of document validation (including PDF validation details)
    
    Args:
        documents_with_content: List of valid documents
        documents_without_content: List of invalid documents with reasons
    """
    total_documents = len(documents_with_content) + len(documents_without_content)
    
    print(f"\n?? Document Validation Results:")
    print(f"   ?? Total documents loaded: {total_documents}")
    print(f"   ? Valid documents: {len(documents_with_content)}")
    print(f"   ? Invalid documents: {len(documents_without_content)}")
    
    if total_documents > 0:
        validation_rate = (len(documents_with_content) / total_documents) * 100
        print(f"   ?? Validation success rate: {validation_rate:.1f}%")
    
    # Analyze document types in valid set
    if documents_with_content:
        doc_types = {}
        for doc in documents_with_content:
            doc_type = doc.metadata.get('file_type', 'unknown')
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        
        print(f"\n?? Valid Documents by Type:")
        for doc_type, count in sorted(doc_types.items()):
            print(f"   {doc_type.upper()}: {count} documents")
    
    if documents_without_content:
        print(f"\n? Invalid Document Analysis:")
        
        # Categorize invalid documents by reason and type
        invalid_categories = {}
        file_type_failures = {}
        
        for doc_info in documents_without_content:
            if " - " in doc_info:
                file_path, reason_full = doc_info.split(" - ", 1)
                reason = reason_full.split(" ")[0]
                invalid_categories[reason] = invalid_categories.get(reason, 0) + 1
                
                # Extract file type for analysis
                file_ext = file_path.split('.')[-1].lower() if '.' in file_path else 'unknown'
                if file_ext not in file_type_failures:
                    file_type_failures[file_ext] = {}
                file_type_failures[file_ext][reason] = file_type_failures[file_ext].get(reason, 0) + 1
        
        for reason, count in sorted(invalid_categories.items()):
            print(f"   {reason}: {count} documents")
        
        # Show failures by file type
        if file_type_failures:
            print(f"\n?? Failures by File Type:")
            for file_type, reasons in file_type_failures.items():
                total_failed = sum(reasons.values())
                print(f"   {file_type.upper()}: {total_failed} failed")
                for reason, count in reasons.items():
                    print(f"     - {reason}: {count}")
        
        # Show examples
        if len(documents_without_content) <= 5:
            print(f"\n   Invalid documents:")
            for doc_info in documents_without_content:
                print(f"     - {doc_info}")
        else:
            print(f"\n   First 5 invalid documents:")
            for doc_info in documents_without_content[:5]:
                print(f"     - {doc_info}")
            print(f"     ... and {len(documents_without_content) - 5} more")
        
        print(f"\n?? Suggestions:")
        print(f"   - Check if files contain readable text")
        print(f"   - Verify .doc files were converted properly")
        print(f"   - For PDF files: ensure they're not encrypted or corrupted")
        print(f"   - Consider adjusting MIN_CHUNK_LENGTH ({50} chars currently)")
        
        # PDF-specific suggestions
        pdf_failures = file_type_failures.get('pdf', {})
        if pdf_failures:
            print(f"   - PDF-specific suggestions:")
            print(f"     • Enable OCR fallback for scanned PDFs")
            print(f"     • Check PDF_MIN_CONTENT_LENGTH setting")
            print(f"     • Verify PDF processing libraries are installed")
    
    if len(documents_with_content) > 0:
        print(f"\n? Proceeding with {len(documents_with_content)} valid documents")
    else:
        print(f"\n? No valid documents found for processing")


def check_processing_requirements(config):
    """
    Check if all requirements for processing are met with enhanced reporting (including PDF requirements)
    
    Args:
        config: Configuration object
    
    Returns:
        tuple: (requirements_met, missing_requirements)
    """
    missing_requirements = []
    warnings = []
    
    print("\n?? Checking Processing Requirements:")
    
    # Check OCR requirements if enabled
    if config.ENABLE_OCR:
        try:
            from ocr_processor import check_ocr_availability
            ocr_available, missing_libs = check_ocr_availability()
            if not ocr_available:
                missing_requirements.extend([f"OCR library: {lib}" for lib in missing_libs])
                print(f"   ?? OCR: ? Missing libraries: {', '.join(missing_libs)}")
            else:
                print(f"   ?? OCR: ? All libraries available")
        except ImportError:
            missing_requirements.append("OCR processor module")
            print(f"   ?? OCR: ? Module not found")
    else:
        print(f"   ?? OCR: ?? Disabled in configuration")
    
    # Check document conversion requirements if enabled
    if getattr(config, 'AUTO_CONVERT_DOC', True):
        try:
            from doc_converter import check_conversion_tools
            tools_info = check_conversion_tools()
            if not tools_info['any_tool_available']:
                missing_requirements.append("Document conversion tools (LibreOffice or Pandoc)")
                print(f"   ?? .doc Conversion: ? No tools available")
            else:
                available_tools = []
                if tools_info['libreoffice_available']:
                    available_tools.append("LibreOffice")
                if tools_info['pandoc_available']:
                    available_tools.append("Pandoc")
                print(f"   ?? .doc Conversion: ? Available: {', '.join(available_tools)}")
        except ImportError:
            missing_requirements.append("Document converter module")
            print(f"   ?? .doc Conversion: ? Module not found")
    else:
        print(f"   ?? .doc Conversion: ?? Disabled in configuration")
    
    # NEW: Check PDF processing requirements if enabled
    if config.is_feature_enabled('enhanced_pdf_processing'):
        print(f"   ?? Enhanced PDF Processing: ? Enabled in configuration")
        
        # Check PDF libraries
        pdf_libs_available = []
        pdf_libs_missing = []
        
        try:
            import fitz
            pdf_libs_available.append("PyMuPDF")
        except ImportError:
            pdf_libs_missing.append("PyMuPDF")
        
        try:
            import pdfplumber
            pdf_libs_available.append("pdfplumber")
        except ImportError:
            pdf_libs_missing.append("pdfplumber")
        
        if config.PDF_ENABLE_OCR_FALLBACK:
            try:
                from pdf2image import convert_from_path
                pdf_libs_available.append("pdf2image")
            except ImportError:
                pdf_libs_missing.append("pdf2image")
        
        if pdf_libs_missing:
            missing_requirements.extend([f"PDF library: {lib}" for lib in pdf_libs_missing])
            print(f"     ?? PDF Libraries: ? Missing: {', '.join(pdf_libs_missing)}")
        else:
            print(f"     ?? PDF Libraries: ? Available: {', '.join(pdf_libs_available)}")
        
        # Check PDF configuration
        pdf_config_issues = []
        if config.PDF_CHUNK_SIZE < 100:
            pdf_config_issues.append(f"PDF_CHUNK_SIZE too small ({config.PDF_CHUNK_SIZE})")
        
        if config.PDF_MIN_CONTENT_LENGTH < 10:
            warnings.append(f"PDF_MIN_CONTENT_LENGTH very low ({config.PDF_MIN_CONTENT_LENGTH})")
        
        if pdf_config_issues:
            missing_requirements.extend(pdf_config_issues)
            print(f"     ?? PDF Config: ? Issues: {', '.join(pdf_config_issues)}")
        else:
            print(f"     ?? PDF Config: ? Valid")
            
    else:
        print(f"   ?? Enhanced PDF Processing: ?? Disabled in configuration")
        warnings.append("Enhanced PDF processing is disabled - PDF files will use basic fallback")
    
    # Check database connection
    if not config.CONNECTION_STRING:
        missing_requirements.append("Database connection string")
        print(f"   ??? Database: ? Connection string missing")
    else:
        print(f"   ??? Database: ? Connection string configured")
    
    # Check required directories
    if not config.DOCUMENTS_DIR:
        missing_requirements.append("Documents directory path")
        print(f"   ?? Documents Dir: ? Path not configured")
    elif not os.path.exists(config.DOCUMENTS_DIR):
        missing_requirements.append(f"Documents directory does not exist: {config.DOCUMENTS_DIR}")
        print(f"   ?? Documents Dir: ? Does not exist: {config.DOCUMENTS_DIR}")
    else:
        print(f"   ?? Documents Dir: ? {config.DOCUMENTS_DIR}")
    
    # Check backup directory setup
    if config.BACKUP_ORIGINAL_DOC:
        backup_dir = config.get_backup_directory()
        backup_parent = os.path.dirname(backup_dir)
        if not os.access(backup_parent, os.W_OK):
            warnings.append(f"No write permission for backup parent directory: {backup_parent}")
            print(f"   ?? Backup Dir: ?? No write permission: {backup_parent}")
        else:
            print(f"   ?? Backup Dir: ? {backup_dir}")
    else:
        print(f"   ?? Backup Dir: ?? Backup disabled")
    
    # Check blacklist configuration
    if config.BLACKLIST_DIRECTORIES:
        print(f"   ?? Blacklist: ? {len(config.BLACKLIST_DIRECTORIES)} directories excluded")
        print(f"      Excluded: {', '.join(config.BLACKLIST_DIRECTORIES[:3])}")
        if len(config.BLACKLIST_DIRECTORIES) > 3:
            print(f"      ... and {len(config.BLACKLIST_DIRECTORIES) - 3} more")
    else:
        warnings.append("No directories blacklisted - backup directories may be processed")
        print(f"   ?? Blacklist: ?? No directories excluded")
    
    # Print summary
    all_good = len(missing_requirements) == 0
    
    if all_good:
        print(f"\n? All processing requirements met!")
        if warnings:
            print(f"?? Warnings: {len(warnings)}")
            for warning in warnings:
                print(f"   - {warning}")
    else:
        print(f"\n? Missing requirements: {len(missing_requirements)}")
        for requirement in missing_requirements:
            print(f"   - {requirement}")
        print(f"\nSome features may not work properly. Consider installing missing components.")
    
    return all_good, missing_requirements


def print_requirements_check(requirements_met, missing_requirements):
    """
    Print requirements check results (legacy function for compatibility)
    
    Args:
        requirements_met: Boolean indicating if all requirements are met
        missing_requirements: List of missing requirements
    """
    if requirements_met:
        print("? All processing requirements met")
    else:
        print("?? Missing requirements detected:")
        for requirement in missing_requirements:
            print(f"   - {requirement}")
        print("\nSome features may not work properly. Consider installing missing components.")


def get_file_processing_summary(text_documents, image_documents, processing_summary):
    """
    Get comprehensive file processing summary with enhanced details (including PDF processing)
    
    Args:
        text_documents: List of text documents
        image_documents: List of image documents
        processing_summary: Processing summary dictionary
    
    Returns:
        dict: Comprehensive processing summary
    """
    summary = {
        'total_files_processed': len(text_documents) + len(image_documents),
        'text_files': len(text_documents),
        'image_files': len(image_documents),
        'processing_time': 0,  # Will be filled by caller
        'conversion_stats': processing_summary.get('conversion_results', {}),
        'ocr_stats': processing_summary.get('ocr_stats', {}),
        'pdf_stats': processing_summary.get('pdf_processing_summary', {}),  # NEW
        'features_used': processing_summary.get('enhanced_features_used', []),
        'blacklist_applied': processing_summary.get('blacklist_applied', False),
        'directories_skipped': processing_summary.get('directories_skipped', 0),
        'backup_directory': processing_summary.get('backup_directory'),
        'processing_quality': 'unknown'
    }
    
    # Determine processing quality
    total_attempted = summary['total_files_processed']
    if total_attempted == 0:
        summary['processing_quality'] = 'no_files'
    else:
        # Calculate quality based on conversion success and features used
        quality_score = 0
        
        # Base score for successful processing
        quality_score += 50
        
        # Bonus for successful conversions
        conversion_stats = summary['conversion_stats']
        if conversion_stats and not conversion_stats.get('skipped'):
            if conversion_stats.get('successful', 0) > 0:
                quality_score += 20
            if conversion_stats.get('backup_created', 0) > 0:
                quality_score += 10
        
        # Bonus for OCR processing
        if summary['ocr_stats'] and summary['ocr_stats'].get('successful', 0) > 0:
            quality_score += 15
        
        # NEW: Bonus for PDF processing
        if summary['pdf_stats'] and summary['pdf_stats'].get('files_processed', 0) > 0:
            quality_score += 20
            # Extra bonus for successful PDF text extraction
            if summary['pdf_stats'].get('text_extracted_chars', 0) > 10000:
                quality_score += 10
        
        # Bonus for blacklist filtering
        if summary['blacklist_applied']:
            quality_score += 5
        
        # Determine quality level
        if quality_score >= 95:
            summary['processing_quality'] = 'excellent'
        elif quality_score >= 75:
            summary['processing_quality'] = 'good'
        elif quality_score >= 50:
            summary['processing_quality'] = 'basic'
        else:
            summary['processing_quality'] = 'poor'
    
    return summary


def get_loading_recommendations(processing_summary, config):
    """
    Get recommendations for improving loading performance (including PDF recommendations)
    
    Args:
        processing_summary: Processing summary dictionary
        config: Configuration object
    
    Returns:
        list: List of recommendations
    """
    recommendations = []
    
    # Check conversion results
    conversion_results = processing_summary.get('conversion_results', {})
    if conversion_results and not conversion_results.get('skipped'):
        failed_conversions = conversion_results.get('failed', 0)
        total_conversions = conversion_results.get('attempted', 0)
        
        if failed_conversions > 0 and total_conversions > 0:
            failure_rate = (failed_conversions / total_conversions) * 100
            if failure_rate > 20:
                recommendations.append(f"High .doc conversion failure rate ({failure_rate:.1f}%). Consider installing both LibreOffice and Pandoc for better compatibility.")
    
    # NEW: Check PDF processing results
    pdf_stats = processing_summary.get('pdf_processing_summary', {})
    if pdf_stats:
        pdf_files = pdf_stats.get('files_processed', 0)
        if pdf_files > 0:
            # Check method usage for optimization suggestions
            method_usage = pdf_stats.get('method_usage', {})
            ocr_fallback_count = method_usage.get('ocr_fallback', 0)
            failed_count = method_usage.get('failed_extractions', 0)
            
            if failed_count > 0:
                failure_rate = (failed_count / pdf_files) * 100
                if failure_rate > 10:
                    recommendations.append(f"High PDF processing failure rate ({failure_rate:.1f}%). Check PDF file integrity and enable OCR fallback.")
            
            if ocr_fallback_count > pdf_files * 0.5:  # More than 50% using OCR
                recommendations.append(f"Many PDFs requiring OCR fallback ({ocr_fallback_count}/{pdf_files}). Consider optimizing OCR settings or PDF preprocessing.")
            
            # Performance recommendations
            avg_speed = pdf_stats.get('processing_speed', 0)
            if avg_speed > 0 and avg_speed < 1:  # Less than 1 page per second
                recommendations.append(f"Slow PDF processing speed ({avg_speed:.2f} pages/sec). Consider enabling PyMuPDF preference and disabling unnecessary features.")
            
            # Content extraction recommendations
            avg_chars = pdf_stats.get('average_chars_per_page', 0)
            if avg_chars < 100:  # Very low text extraction
                recommendations.append(f"Low text extraction from PDFs ({avg_chars:.0f} chars/page). Enable OCR fallback and check PDF quality.")
    
    # Check blacklist usage
    if not processing_summary.get('blacklist_applied', False):
        recommendations.append("Consider enabling blacklist filtering to exclude backup and temporary directories.")
    
    # Check OCR performance
    ocr_stats = processing_summary.get('ocr_stats', {})
    if ocr_stats:
        ocr_success_rate = ocr_stats.get('success_rate', 0)
        if ocr_success_rate < 50:
            recommendations.append(f"Low OCR success rate ({ocr_success_rate:.1f}%). Consider adjusting OCR quality threshold or enabling auto-rotation.")
    
    # Check directory structure
    directories_skipped = processing_summary.get('directories_skipped', 0)
    directories_scanned = processing_summary.get('directories_scanned', 0)
    
    if directories_scanned > 0:
        skip_rate = (directories_skipped / directories_scanned) * 100
        if skip_rate > 30:
            recommendations.append(f"High directory skip rate ({skip_rate:.1f}%). Review blacklist settings to ensure important directories aren't excluded.")
    
    # Performance recommendations
    total_files = processing_summary.get('total_files_processed', 0)
    if total_files > 10000:
        recommendations.append("Large number of files detected. Consider increasing PROCESSING_BATCH_SIZE for better performance.")
    
    # NEW: PDF-specific performance recommendations
    directory_analysis = processing_summary.get('directory_analysis', {})
    if directory_analysis and 'pdf_analysis' in directory_analysis:
        pdf_analysis = directory_analysis['pdf_analysis']
        
        if pdf_analysis.get('total_pdfs', 0) > 100:
            recommendations.append("Large number of PDFs detected. Consider enabling PDF processing optimizations and parallel processing.")
        
        # Large PDF recommendations
        size_analysis = pdf_analysis.get('size_analysis', {})
        if size_analysis.get('large_pdfs'):
            large_count = len(size_analysis['large_pdfs'])
            if large_count > 10:
                recommendations.append(f"{large_count} large PDFs detected. Consider increasing PDF processing timeouts and memory allocation.")
    
    if not recommendations:
        recommendations.append("Current loading configuration appears optimal.")
    
    return recommendations


def analyze_processing_performance(processing_summary, loading_time):
    """
    NEW: Analyze processing performance including PDF performance metrics
    
    Args:
        processing_summary: Processing summary dictionary
        loading_time: Total loading time
    
    Returns:
        dict: Performance analysis
    """
    total_files = processing_summary.get('total_files_processed', 0)
    
    performance_analysis = {
        'total_files': total_files,
        'total_time': loading_time,
        'overall_speed': total_files / loading_time if loading_time > 0 else 0,
        'file_type_performance': {},
        'feature_performance': {},
        'bottlenecks': [],
        'optimization_suggestions': []
    }
    
    # Analyze performance by file type
    conversion_stats = processing_summary.get('conversion_results', {})
    if conversion_stats and not conversion_stats.get('skipped'):
        doc_files = conversion_stats.get('attempted', 0)
        if doc_files > 0:
            performance_analysis['file_type_performance']['doc_conversion'] = {
                'files': doc_files,
                'success_rate': (conversion_stats.get('successful', 0) / doc_files * 100)
            }
    
    # NEW: PDF performance analysis
    pdf_stats = processing_summary.get('pdf_processing_summary', {})
    if pdf_stats:
        pdf_files = pdf_stats.get('files_processed', 0)
        pdf_pages = pdf_stats.get('total_pages', 0)
        pdf_speed = pdf_stats.get('processing_speed', 0)
        
        if pdf_files > 0:
            performance_analysis['file_type_performance']['pdf_processing'] = {
                'files': pdf_files,
                'pages': pdf_pages,
                'pages_per_second': pdf_speed,
                'chars_extracted': pdf_stats.get('text_extracted_chars', 0),
                'avg_chars_per_page': pdf_stats.get('average_chars_per_page', 0)
            }
            
            # Identify PDF bottlenecks
            if pdf_speed < 2:  # Less than 2 pages per second
                performance_analysis['bottlenecks'].append('Slow PDF processing speed')
                performance_analysis['optimization_suggestions'].append('Enable PyMuPDF preference and optimize PDF settings')
            
            method_usage = pdf_stats.get('method_usage', {})
            ocr_usage = method_usage.get('ocr_fallback', 0)
            if ocr_usage > pdf_files * 0.3:  # More than 30% using OCR
                performance_analysis['bottlenecks'].append('High OCR fallback usage')
                performance_analysis['optimization_suggestions'].append('Improve PDF quality or preprocessing to reduce OCR dependency')
    
    # OCR performance analysis
    ocr_stats = processing_summary.get('ocr_stats', {})
    if ocr_stats:
        ocr_files = ocr_stats.get('total_found', 0)
        ocr_success = ocr_stats.get('successful', 0)
        
        if ocr_files > 0:
            performance_analysis['file_type_performance']['ocr_processing'] = {
                'files': ocr_files,
                'success_rate': (ocr_success / ocr_files * 100),
                'text_extracted': ocr_stats.get('total_text_length', 0)
            }
    
    # Feature performance analysis
    features_used = processing_summary.get('enhanced_features_used', [])
    performance_analysis['feature_performance'] = {
        'features_enabled': len(features_used),
        'advanced_features_used': any('Enhanced' in feature or 'Advanced' in feature for feature in features_used)
    }
    
    return performance_analysis


def print_performance_analysis(performance_analysis):
    """
    NEW: Print detailed performance analysis including PDF metrics
    
    Args:
        performance_analysis: Results from analyze_processing_performance
    """
    print(f"\n? PERFORMANCE ANALYSIS:")
    print(f"   ?? Total files: {performance_analysis['total_files']:,}")
    print(f"   ?? Total time: {performance_analysis['total_time']:.2f}s")
    print(f"   ?? Overall speed: {performance_analysis['overall_speed']:.2f} files/sec")
    
    # File type performance
    file_perf = performance_analysis['file_type_performance']
    if file_perf:
        print(f"\n?? File Type Performance:")
        
        if 'doc_conversion' in file_perf:
            doc_perf = file_perf['doc_conversion']
            print(f"   DOC Conversion: {doc_perf['files']} files, {doc_perf['success_rate']:.1f}% success")
        
        if 'pdf_processing' in file_perf:
            pdf_perf = file_perf['pdf_processing']
            print(f"   PDF Processing: {pdf_perf['files']} files, {pdf_perf['pages']} pages")
            print(f"     Speed: {pdf_perf['pages_per_second']:.2f} pages/sec")
            print(f"     Text: {pdf_perf['chars_extracted']:,} chars, {pdf_perf['avg_chars_per_page']:.0f} chars/page")
        
        if 'ocr_processing' in file_perf:
            ocr_perf = file_perf['ocr_processing']
            print(f"   OCR Processing: {ocr_perf['files']} files, {ocr_perf['success_rate']:.1f}% success")
            print(f"     Text extracted: {ocr_perf['text_extracted']:,} chars")
    
    # Bottlenecks and suggestions
    if performance_analysis['bottlenecks']:
        print(f"\n?? Performance Bottlenecks:")
        for bottleneck in performance_analysis['bottlenecks']:
            print(f"   - {bottleneck}")
    
    if performance_analysis['optimization_suggestions']:
        print(f"\n?? Optimization Suggestions:")
        for suggestion in performance_analysis['optimization_suggestions']:
            print(f"   - {suggestion}")
    
    # Feature performance
    feature_perf = performance_analysis['feature_performance']
    print(f"\n? Feature Usage:")
    print(f"   Features enabled: {feature_perf['features_enabled']}")
    print(f"   Advanced features: {'?' if feature_perf['advanced_features_used'] else '?'}")


def create_comprehensive_loading_report(text_documents, image_documents, processing_summary, loading_time, config):
    """
    NEW: Create a comprehensive loading report including all processing aspects
    
    Args:
        text_documents: List of text documents
        image_documents: List of image documents
        processing_summary: Processing summary dictionary
        loading_time: Total loading time
        config: Configuration object
    
    Returns:
        dict: Comprehensive loading report
    """
    # Get file processing summary
    file_summary = get_file_processing_summary(text_documents, image_documents, processing_summary)
    file_summary['processing_time'] = loading_time
    
    # Get performance analysis
    performance_analysis = analyze_processing_performance(processing_summary, loading_time)
    
    # Get recommendations
    recommendations = get_loading_recommendations(processing_summary, config)
    
    # Create comprehensive report
    comprehensive_report = {
        'timestamp': datetime.now().isoformat(),
        'file_summary': file_summary,
        'performance_analysis': performance_analysis,
        'recommendations': recommendations,
        'configuration_used': {
            'documents_dir': config.DOCUMENTS_DIR,
            'auto_convert_doc': config.AUTO_CONVERT_DOC,
            'enable_ocr': config.ENABLE_OCR,
            'enhanced_pdf_processing': config.is_feature_enabled('enhanced_pdf_processing'),
            'blacklist_directories': config.BLACKLIST_DIRECTORIES,
            'chunk_size': config.CHUNK_SIZE,
            'batch_size': config.PROCESSING_BATCH_SIZE
        },
        'processing_summary': processing_summary
    }
    
    return comprehensive_report


def print_comprehensive_loading_report(comprehensive_report):
    """
    NEW: Print the comprehensive loading report
    
    Args:
        comprehensive_report: Report from create_comprehensive_loading_report
    """
    print(f"\n?? COMPREHENSIVE LOADING REPORT")
    print(f"Generated: {comprehensive_report['timestamp']}")
    print("=" * 60)
    
    # File summary
    file_summary = comprehensive_report['file_summary']
    print(f"\n?? File Processing Summary:")
    print(f"   Total files: {file_summary['total_files_processed']}")
    print(f"   Text files: {file_summary['text_files']}")
    print(f"   Image files: {file_summary['image_files']}")
    print(f"   Processing time: {file_summary['processing_time']:.2f}s")
    print(f"   Quality: {file_summary['processing_quality'].title()}")
    
    # Performance analysis
    print_performance_analysis(comprehensive_report['performance_analysis'])
    
    # Configuration used
    config_used = comprehensive_report['configuration_used']
    print(f"\n?? Configuration Used:")
    print(f"   Documents directory: {config_used['documents_dir']}")
    print(f"   Auto .doc conversion: {'?' if config_used['auto_convert_doc'] else '?'}")
    print(f"   OCR processing: {'?' if config_used['enable_ocr'] else '?'}")
    print(f"   Enhanced PDF processing: {'?' if config_used['enhanced_pdf_processing'] else '?'}")
    print(f"   Blacklist filtering: {'?' if config_used['blacklist_directories'] else '?'}")
    
    # Recommendations
    recommendations = comprehensive_report['recommendations']
    if recommendations:
        print(f"\n?? Recommendations:")
        for rec in recommendations:
            print(f"   - {rec}")
    
    print("=" * 60)