#
#   Loads Koondkorpus XML TEI files (either from zipped archives, or from directories where
#  the files have been unpacked), creates EstNLTK Text objects based on these files, adds
#  tokenization to Texts (optional), and stores Texts in a PostgreSQL collection.
#   Note: If the given collection already exists, it will be deleted, and a new collection
#  will be created for storing Texts.
# 

import os, sys
import os.path
import argparse
from argparse import RawTextHelpFormatter

import logging

from collections import OrderedDict

from datetime import datetime
from datetime import timedelta

from estnltk.layer_operations import split_by

from estnltk.corpus_processing.parse_koondkorpus import get_div_target
from estnltk.corpus_processing.parse_koondkorpus import get_text_subcorpus_name
from estnltk.corpus_processing.parse_koondkorpus import parse_tei_corpus
from estnltk.corpus_processing.parse_koondkorpus import unpack_zipped_xml_files_iterator
from estnltk.corpus_processing.parse_koondkorpus import parse_tei_corpus_file_content

from estnltk.storage.postgres import PostgresStorage

def iter_unpacked_xml(root_dir, encoding='utf-8', create_empty_docs=True,\
                     add_tokenization=False, \
                     preserve_tokenization=False, \
                     sentence_separator='\n', \
                     paragraph_separator='\n\n' ):
    """ Traverses recursively root_dir to find XML TEI documents,
        converts found documents to EstNLTK Text objects, and 
        yields created Text objects.
    
        Parameters
        ----------
        root_dir: str
            The root directory which is recursively traversed to find 
            XML files;
        encoding: str
            Encoding of the XML files. (default: 'utf-8')
        create_empty_docs: boolean
            If True, then documents are also created if there is no 
            textual content, but only metadata content.
            Note: an empty document may be a captioned table or a figure, 
            which content has been removed from the XML file. Depending on 
            the goals of the analysis, the caption may still be useful, 
            so, by default, empty documents are preserved;
            (default: True)
        add_tokenization: boolean
            If True, then tokenization layers 'tokens', 'compound_tokens', 
            'words', 'sentences', 'paragraphs' will be added to all newly created 
            Text instances;
            If preserve_orig_tokenization is set, then original tokenization in 
            the document will be preserved; otherwise, the tokenization will be
            created with EstNLTK's default tokenization tools;
            (Default: False)
        preserve_tokenization: boolean
            If True, then the original segmentation from the XML file (sentences 
            between <s> and </s>, paragraphs between <p> and </p>, and words &
            tokens separated by spaces) is also preserved in the newly created Text 
            instances;
            Note: this only has effect if add_tokenization has been switched on;
            (Default: False)
        sentence_separator: str
            String to be used as a sentence separator during the reconstruction
            of the text. The parameter value should be provided, None is not 
            allowed.
            (Default: '\n')
        paragraph_separator: str
            String to be used as a paragraph separator during the reconstruction
            of the text. The parameter value should be provided, None is not 
            allowed.
            (Default: '\n\n')
    """
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if len(dirnames) > 0 or len(filenames) == 0 or 'bin' in dirpath:
            continue
        for fnm in filenames:
            full_fnm = os.path.join(dirpath, fnm)
            target   = get_div_target(full_fnm)
            docs = parse_tei_corpus(full_fnm, target=[target], encoding=encoding, \
                                    add_tokenization=add_tokenization, \
                                    preserve_tokenization=preserve_tokenization, \
                                    sentence_separator=sentence_separator,\
                                    paragraph_separator=paragraph_separator,\
                                    record_xml_filename=True)
            for doc_id, doc in enumerate(docs):
                if not create_empty_docs and len(doc.text) == 0:
                   # Skip an empty document
                   continue
                yield doc


log = None

def iter_packed_xml(root_dir, encoding='utf-8', create_empty_docs=True,\
                     add_tokenization=False, \
                     preserve_tokenization=False, \
                     sentence_separator='\n', \
                     paragraph_separator='\n\n' ):
    """ Finds zipped (.zip and tar.gz) files from the directory root_dir, 
        unpacks XML TEI documents from zipped files, converts documents 
        to EstNLTK Text objects, and yields created Text objects.
    
        Parameters
        ----------
        root_dir: str
            The root directory which contains zipped (.zip and tar.gz) 
            XML TEI files;
        encoding: str
            Encoding of the XML files. (default: 'utf-8')
        create_empty_docs: boolean
            If True, then documents are also created if there is no 
            textual content, but only metadata content.
            Note: an empty document may be a captioned table or a figure, 
            which content has been removed from the XML file. Depending on 
            the goals of the analysis, the caption may still be useful, 
            so, by default, empty documents are preserved;
            (default: True)
        add_tokenization: boolean
            If True, then tokenization layers 'tokens', 'compound_tokens', 
            'words', 'sentences', 'paragraphs' will be added to all newly created 
            Text instances;
            If preserve_orig_tokenization is set, then original tokenization in 
            the document will be preserved; otherwise, the tokenization will be
            created with EstNLTK's default tokenization tools;
            (Default: False)
        preserve_tokenization: boolean
            If True, then the original segmentation from the XML file (sentences 
            between <s> and </s>, paragraphs between <p> and </p>, and words &
            tokens separated by spaces) is also preserved in the newly created Text 
            instances;
            Note: this only has effect if add_tokenization has been switched on;
            (Default: False)
        sentence_separator: str
            String to be used as a sentence separator during the reconstruction
            of the text. The parameter value should be provided, None is not 
            allowed.
            (Default: '\n')
        paragraph_separator: str
            String to be used as a paragraph separator during the reconstruction
            of the text. The parameter value should be provided, None is not 
            allowed.
            (Default: '\n\n')
    """
    #global log
    files = os.listdir( root_dir )
    for in_file in files:
        if in_file.endswith('.zip') or in_file.endswith('.gz'):
           in_path = os.path.join(root_dir, in_file)
           for (full_fnm, content) in unpack_zipped_xml_files_iterator(in_path,test_only=False):
               div_target = get_div_target(full_fnm)
               #log.debug('Loading '+full_fnm+' with '+div_target)
               docs = parse_tei_corpus_file_content(content, full_fnm, target=[div_target],\
                                                             add_tokenization=add_tokenization, \
                                                             preserve_tokenization=preserve_tokenization, \
                                                             sentence_separator=sentence_separator,\
                                                             paragraph_separator=paragraph_separator,\
                                                             record_xml_filename=True)
               for doc_id, doc in enumerate(docs):
                   if not create_empty_docs and len(doc.text) == 0:
                      # Skip an empty document
                      continue
                   yield doc


#
# The following iterator functions borrow from Paul's source at:
#      .../estnltk_workflows/postgres_collections/data_import/create_collection.py
#

# function that keeps the original text without splitting
def to_text(text):
    yield text, None, None

# function that splits the original text into paragraphs
def to_paragraphs(text):
    for para_nr, para in enumerate(split_by(text, layer='paragraphs',
                                            layers_to_keep=['tokens', 'compound_tokens', 'words', 'sentences']), start=1):
        yield para, para_nr, None

# function that splits the original text into sentences
def to_sentences(text):
    sent_nr = 0
    for para_nr, para in enumerate(split_by(text, layer='paragraphs',
                                            layers_to_keep=['tokens', 'compound_tokens', 'words', 'sentences']), start=1):
        for sent in split_by(para, layer='sentences', layers_to_keep=['tokens', 'compound_tokens', 'words']):
            sent_nr += 1
            yield sent, para_nr, sent_nr


def process_files(rootdir, doc_iterator, collection, encoding='utf-8', \
                  create_empty_docs=False, logger=None, tokenization=None,\
                  force_sentence_end_newlines=False, splittype='no_splitting',\
                  metadata_extent='complete'):
    """ Uses given doc_iterator (iter_packed_xml or iter_unpacked_xml) to
        extract texts from the files in the folder root_dir.
        Optionally, adds tokenization layers to created Text objects.
    
        Parameters
        ----------
        root_dir: str
            The root directory which contains XML TEI files that 
            doc_iterator can extract;
        doc_iterator: iter_packed_xml or iter_unpacked_xml
            Iterator function that can extract Text objects from 
            (packed or unpacked) files in the root_dir;
        collection:  estnltk.storage.postgres.db.PgCollection
            EstNLTK's PgCollection where extracted Texts should be 
            stored;
        encoding: str
            Encoding of the XML files. (default: 'utf-8')
        create_empty_docs: boolean
            If True, then documents are also created if there is no 
            textual content, but only metadata content.
            (default: False)
        logger: logging.Logger
            Logger used for debugging messages;
        tokenization: ['none', 'preserve', 'estnltk']
            specifies if tokenization will be added to Texts, and if 
            so, then how it will be added. 
            * 'none'     -- text   will   be   created  without  any 
                            tokenization layers;
            * 'preserve' -- original tokenization from XML files will 
                            be preserved in layers of the text; 
            * 'estnltk'  -- text's original tokenization will be 
                            overwritten by estnltk's tokenization;
        force_sentence_end_newlines: boolean
            If set, then during the reconstruction of a text string, 
            sentence endings from the original XML mark-up will always 
            be marked with newlines in the text string, regardless 
            the tokenization option used.
            (default: False)
        splittype: ['no_splitting', 'sentences', 'paragraphs']
            specifies if and how texts should be split before inserting
            into the database:
            * 'no_splitting' -- insert full texts, do no split;
            * 'sentences'    -- split into sentences (a Text object 
                                for each sentence), and insert 
                                sentences into database;
            * 'paragraphs'   -- split into paragraphs (a Text object 
                                for each paragraph), and insert 
                                paragraphs into database;
        metadata_extent: ['minimal', 'complete']
            specifies to which extent created Text object should be 
            populated with metadata. 
            (default: 'complete')
    """
    global special_tokens_tagger
    global special_compound_tokens_tagger
    global special_sentence_tokenizer
    assert doc_iterator in [iter_unpacked_xml, iter_packed_xml]
    assert tokenization in [None, 'none', 'preserve', 'estnltk']
    assert splittype in ['no_splitting', 'sentences', 'paragraphs']
    assert metadata_extent in ['minimal', 'complete']
    add_tokenization      = False
    preserve_tokenization = False
    sentence_separator    = ' '
    paragraph_separator   = '\n\n'
    if tokenization:
        if tokenization == 'none':
           tokenization = None
        if tokenization == 'preserve':
           add_tokenization      = True
           preserve_tokenization = True
           sentence_separator    = '\n'
        elif tokenization == 'estnltk':
           add_tokenization      = True
           preserve_tokenization = False
    if force_sentence_end_newlines:
        sentence_separator = '\n'
    # Choose how the loaded document will be 
    # split before the insertion
    split = to_text
    if args.splittype == 'no_splitting':
        split = to_text
    elif args.splittype == 'sentences':
       split = to_sentences
    elif args.splittype == 'paragraphs':
       split = to_paragraphs
    doc_id = 1
    for doc in doc_iterator(rootdir, encoding=encoding, create_empty_docs=create_empty_docs, \
                            add_tokenization=add_tokenization, preserve_tokenization=preserve_tokenization,\
                            sentence_separator=sentence_separator, paragraph_separator=paragraph_separator):
        # Split the loaded document into smaller units if required
        for doc_fragment, para_nr, sent_nr in split( doc ):
            meta = {}
            # Gather metadata
            # 1) minimal metadata:
            meta['file'] = doc.meta['_xml_file'] if '_xml_file' in doc.meta else ''
            doc_fragment.meta['file'] = meta['file']
            if para_nr is not None:
               meta['document_nr'] = doc_id
               doc_fragment.meta['doc_nr'] = doc_id
               meta['paragraph_nr'] = para_nr
               doc_fragment.meta['para_nr'] = para_nr
            if sent_nr is not None:
               meta['sentence_nr'] = sent_nr
               doc_fragment.meta['sent_nr'] = sent_nr
            # 2) complete metadata:
            if metadata_extent == 'complete':
               for key, value in doc.meta.items():
                   doc_fragment.meta[key] = value
               if '_xml_file' in doc.meta:
                   # record subcorpus name
                   subcorpus = get_text_subcorpus_name( None, doc.meta['_xml_file'], doc, expand_names=False )
                   doc_fragment.meta['subcorpus'] = subcorpus
               # Collect remaining metadata
               for key in ['subcorpus', 'title', 'type']:
                   meta[key] = doc_fragment.meta[key] if key in doc_fragment.meta else ''
            # Finally, insert document 
            row_id = collection.insert(doc_fragment, meta_data=meta)
            if logger:
               # debugging stuff
               with_layers = list(doc_fragment.layers.keys())
               if with_layers:
                  with_layers = ' with layers '+str(with_layers)
               else:
                  with_layers = ''
               logger.debug((' Text #{}'+with_layers+' inserted.').format(row_id))
               #logger.debug('  Metadata: {}'.format(doc_fragment.meta))
        doc_id += 1
        #print('.', end = '')
        #sys.stdout.flush()
    print()



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=
       "Loads Koondkorpus XML TEI files (either from zipped archives, or from directories where \n"+\
       "the files have been unpacked), creates EstNLTK Text objects based on these files, adds \n"+\
       "tokenization to Texts (optional), splits Texts into paragraphs or sentences (optional),\n"+\
       "and stores Texts in a PostgreSQL collection.\n"+\
       "Note: If the given collection already exists, it will be deleted, and a new collection \n"+\
       "will be created for storing Texts.",\
       formatter_class=RawTextHelpFormatter
    )
    # 1) Input parameters
    parser.add_argument('rootdir', type=str, \
                        help='the directory containing input corpus files (packed or unpacked)')
    parser.add_argument('-e', '--encoding', type=str, default='utf-8', \
                        help='encoding of the TEI XML files (Default: utf-8).')
    parser.add_argument('-i', '--input_format', dest='input_format', \
                        help='specifies format of the input files:\n\n'+\
                             '* unzipped -- rootdir will be traversed recursively for\n'+\
                             '  XML TEI files of the Koondkorpus. The target files should\n'+\
                             '  be unpacked, but they must be inside the same directory\n'+\
                             '  structure as they were in the packages.\n'+\
                             '\n'+\
                             ' * zipped -- rootdir will be traversed (non-recursively)\n'+\
                             "   for .zip and .gz files. Each archive file will be opened,\n"+\
                             "   and XML TEI files will be extracted.\n"+\
                             '(default: zipped).',\
                        choices=['zipped', 'unzipped'], \
                        default='zipped' )
    # 2) Output parameters: database access
    parser.add_argument('--pgpass', dest='pgpass', action='store', \
                        default='~/.pgpass', \
                        help='name of the PostgreSQL password file (default: ~/.pgpass).\n'+\
                             'The format of the file should be: \n'+\
                             '       hostname:port:database:username:password ')
    parser.add_argument('--schema', dest='schema', action='store',\
                        default='public',\
                        help='name of the collection schema (default: public)')
    parser.add_argument('--collection', dest='collection', action='store',
                        default='collection',
                        help='name of the collection (default: collection)')
    parser.add_argument('--role', dest='role', action='store',
                        help='collection owner (default: None)')
    # 3) Processing parameters 
    parser.add_argument('-t', '--tokenization', dest='tokenization', \
                        help='specifies if and how texts will be reconstructed and tokenized: \n\n'+ \
                             '* none -- the text string will be reconstructed by joining words \n'+\
                             '  and sentences from the original XML mark-up by spaces, and paragraphs\n'+\
                             '  by double newlines. Tokenization layers will not be created.\n\n'+\
                             
                             '* preserve -- the text string will be reconstructed by joining \n'+\
                             '  words from the original XML mark-up by spaces, sentences by \n'+\
                             '  newlines, and paragraphs by double newlines. Tokenization layers \n'+\
                             '  will be created, and they\'ll preserve the original tokenization \n'+\
                             '  of XML files.\n'+\
                             "    Note #1: tokenization layers 'tokens', 'compound_tokens', \n"+\
                             "    'words', 'sentences', 'paragraphs' will be created;\n"+\
                             "    Note #2: the layer 'compound_tokens' will always remain empty \n"+\
                             '    because koondkorpus files do no contain information about token \n'+\
                             '    compounding;\n'+\
                             "    Note #3: the layer 'tokens' will be equal to the layer 'words';"+\
                             '  \n\n'+\

                             '* estnltk -- the text string will be reconstructed by joining words \n'+\
                             '  and sentences from the original XML mark-up by spaces, and \n'+\
                             "  paragraphs by double newlines. Tokenization layers will be created \n"+\
                             "  with EstNLTK's default tokenizers, overwriting the original \n"+\
                             '  tokenization mark-up from XML files.\n'
                             "    Note #1: tokenization layers 'tokens', 'compound_tokens', \n"+\
                             "    'words', 'sentences', 'paragraphs' will be created;\n"+\
                             "(default: none)",\
                        choices=['none', 'preserve', 'estnltk'], \
                        default='none' )
    parser.add_argument('--splittype', dest='splittype', action='store',
                        default='no_splitting', choices=['no_splitting', 'sentences', 'paragraphs'],
                        help='specifies if and how the source texts should be split before\n'+
                             'inserting into the database. Options:\n'+
                             '\n'+
                             '* no_splitting -- each source text will be inserted into the database\n'+\
                             '  as whole, without any splitting applied;\n'+\
                             '\n'+
                             '* paragraphs -- source texts will split into paragraphs (a Text object\n'+\
                             '  will be created for each paragraph), and then inserted into the\n'+\
                             '  database;\n'
                             '\n'+
                             '* sentences -- source texts will split into sentences (a Text object\n'+\
                             '  will be created for each sentence), and then inserted into the\n'+\
                             '  database;\n'+\
                             '(default: no_splitting)\n\n'
                             '(!) Note: you can only use --splittype if tokenization is turned on!'
                        )
    parser.add_argument('-f', '--force_sentence_end_newlines', dest='force_sentence_end_newlines', \
                        default=False, \
                        action='store_true', \
                        help="If set, then during the reconstruction of a text string, sentence \n"+
                             "endings from the original XML mark-up will always be marked with\n"+
                             "newlines in the text string, regardless the tokenization option\n"+\
                             "used.\n"
                             "You can use this option if you want to replace spaces between the \n"+\
                             "original sentences with newlines when using the tokenization options\n"+\
                             " -t none, or -t estnltk.\n"+\
                             "(default: False)",\
                        )
    parser.add_argument('-m', '--metadata_extent', dest='metadata_extent', \
                        help='specifies to which extent created Text objects should be \n'+\
                             'populated with metadata. Options:\n\n'
                             ' * minimal -- minimal amount of metadata. Fields: \n'+\
                             "      1. 'file'         -- the XML file name; \n"+\
                             "      2. 'document_nr'  -- unique number for the document; \n"+\
                             "          (if text was split into paragraphs or sentences);\n"+\
                             "      3. 'paragraph_nr' -- paragraph's number in the document\n"+\
                             "          (if text was split into paragraphs or sentences);\n"+\
                             "      4. 'sentence_nr'  -- sentence's number in the document\n"+\
                             "          (if text was split into sentences);\n"+\
                             '\n'+\
                             ' * complete -- all metadata included. Fields: \n'+\
                             "      1. 'file'         -- the XML file name; \n"+\
                             "      2. 'document_nr'  -- unique number for the document; \n"+\
                             "          (if text was split into paragraphs or sentences);\n"+\
                             "      3. 'paragraph_nr' -- paragraph's number in the document\n"+\
                             "          (if text was split into paragraphs or sentences);\n"+\
                             "      4. 'sentence_nr'  -- sentence's number in the document\n"+\
                             "          (if text was split into sentences);\n"+\
                             "      5. 'subcorpus'    -- short name of the subcorpus; \n"+\
                             "      6. 'title'        -- title of the document (if available); \n"+\
                             "      7. 'type'         -- type of the document (if available); \n"+\
                             '(default: complete)',\
                        choices=['minimal', 'complete'], \
                        default='complete' )
    # 4) Logging parameters
    parser.add_argument('--logging', dest='logging', action='store', default='info',\
                        choices=['debug', 'info', 'warning', 'error', 'critical'],\
                        help='logging level (default: info)')
    args = parser.parse_args()

    if not os.path.isdir(args.rootdir):
       print('(!) Argument rootdir should be a directory')
       arg_parser.print_help()
    doc_iterator = None 
    if args.input_format == 'zipped':
       doc_iterator = iter_packed_xml
    elif args.input_format == 'unzipped':
       doc_iterator = iter_unpacked_xml
    if not doc_iterator:
       raise Exception('(!) No iterator implemented for the input format',args.input_format)
    if args.splittype != 'no_splitting':
       if args.tokenization == 'none':
          raise Exception('(!) splittype '+str(args.splittype)+' cannot be used without tokenization!')
    logging.basicConfig( level=(args.logging).upper() )
    log = logging.getLogger(__name__)
    
    storage = PostgresStorage(pgpass_file=args.pgpass,
                              schema=args.schema,
                              role=args.role)
    collection = storage.get_collection(args.collection)
    if collection.exists():
        log.info(' Collection {!r} exists. Overwriting.'.format(args.collection))
        collection.delete()

    if not collection.exists():
         fields = [('file', 'str')]
         if args.splittype == 'sentences':
              fields.append( ('document_nr', 'bigint') )
              fields.append( ('paragraph_nr', 'int') )
              fields.append( ('sentence_nr', 'bigint') )
         elif args.splittype == 'paragraphs':
              fields.append( ('document_nr', 'bigint') )
              fields.append( ('paragraph_nr', 'int') )
         if args.metadata_extent == 'complete':
              fields.append( ('subcorpus', 'str') )
              fields.append( ('title', 'str') )
              fields.append( ('type', 'str') )
         meta_fields = OrderedDict( fields )
         collection = storage.get_collection(args.collection, meta_fields=meta_fields)
         collection.create('collection of estnltk texts with segmentation')
         log.info(' New collection {!r} created.'.format(args.collection))
    
    if args.splittype == 'no_splitting':
         log.info(' Source texts will not be splitted.')
    elif args.splittype == 'sentences':
         log.info(' Source texts will be splitted by sentences.')
    elif args.splittype == 'paragraphs':
         log.info(' Source texts will be splitted by paragraphs.')

    startTime = datetime.now()
    process_files(args.rootdir, doc_iterator, collection, encoding=args.encoding, \
                  create_empty_docs=False, logger=log, tokenization=args.tokenization,\
                  force_sentence_end_newlines=args.force_sentence_end_newlines, \
                  splittype=args.splittype, metadata_extent=args.metadata_extent)
    storage.close()
    time_diff = datetime.now() - startTime
    log.info('Total processing time: {}'.format(time_diff))
       