# Export data from Estnltk PostgreSQL collection

## Export to TEXTA

```bash
estnltk-workflows$ estnltk_workflows/postgres_collections/data_export/export_to_texta.sh
```
If the Text objects contain the `morph_analysis` layer, then `words`, `lemmas` and `partofspeech` data is included.

To include TEXTA facts a csv file containing fact mapping instructions is needed.
See the example file [fact_mapping_example.csv](fact_mapping_example.csv).

For options display help:
```bash
estnltk-workflows$ estnltk_workflows/postgres_collections/data_export/export_to_texta.sh -h
```

Options can be saved in a config fail:
```bash
estnltk-workflows$ estnltk_workflows/postgres_collections/data_export/export_to_texta.sh @estnltk_workflows/postgres_collections/data_export/export_to_texta.conf_example
```
