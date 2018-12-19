# 2DA

The 2da files contains tabular data (2d array).

## Text Format

See official Bioware Documentation.


## Binary Format


### File Structure

| Name        |
|-------------|
| header      |
| columns     |
| row_indices | 
| cell_offsets|
| cell_data   |


### Header

| Name      | Type       | Description  |
|-----------|------------|--------------|
| file_type | 4 chars    | "2DA "       |
| version   | 4 chars    | "V2.b"       |


### Columns

| Name            | Type              | Description  |
|-----------------|-------------------|--------------|
| n * column_name | n * chars + byte  | each column name is terminated by tab char (0x09). |
| Terminator      | byte | The end of the list is indicated by a 0x00 byte.        |

### Row Indices

| Name            | Type              | Description  |
|-----------------|-------------------|--------------|
| row_count       | dword             | # of rows    |
| n * row_index   | n * chars + byte  | each row name is terminated by tab char (0x09). n = row count|

Note: The row index list is not terminated by 0x00 byte. Just read as many row indices as indicated by row_count

### Cell Offsets

| Name            | Type              | Description           |
|-----------------|-------------------|-----------------------|
| n * cell_offset | word              | offset into cell_data |

Note: there are row_count * # of column_names cells in the table and therefore as many cell_offsets. cell_offset is relative to cell data


### Cell Data

| Name            | Type              | Description           |
|-----------------|-------------------|-----------------------|
| cell_data_size  | word              | size of cell data in bytes |
| n * cell_content| n * chars + byte  | cell content terminated by 0x00 |

For each cell (row major order) get the offset from cell offsets and read the content relative to cell data position (just after cell_data_size). The cell content is terminated by a null byte (0x00). An empty cell is immediately terminated by 0x00.

