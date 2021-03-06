# Comparing different versions of morphological analysis annotations

Scripts for running Vabamorf's morphological analyzer on a PostgreSQL collection that has morphological annotations, and comparing old and new morphological annotations.

Requirements: Python 3.6+, [Psycopg 2](https://www.psycopg.org), EstNLTK v1.6.8+

* `diff_vm_bin.py` -- Runs VabamorfTagger with given binary lexicons on a morphologically annotated PostgreSQL collection. Finds differences between old and new morphological annotations. Outputs summarized statistics about differences, and writes all differences into a file. For detailed usage information, run: `python diff_vm_bin.py -h`

* `diff_vm_textbased_disambiguation.py` -- Runs VabamorfTagger with text-based disambiguation on a morphologically annotated PostgreSQL collection. Finds differences between old and new morphological annotations. Outputs summarized statistics about differences, and writes all differences into a file. For detailed usage information, run: `python diff_vm_textbased_disambiguation.py -h`

* `diff_vm_existing_layers.py` -- Compares two existing layers of (Vabamorf's) morphological annotations in PostgreSQL collection. Finds annotation differences of two layers. Outputs summarized statistics about differences, and writes all differences into a file. For detailed usage information, run: `python diff_vm_existing_layers.py -h`

* `pick_randomly_from_diffs.py` -- Selects a random subset of differences from an output file produced by a difference finding script. For detailed usage information, run: `python pick_randomly_from_diffs.py -h`
 
