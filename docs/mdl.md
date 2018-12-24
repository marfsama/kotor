# Model file

## Analysis of Data Blocks in Nodes Chunk

* Model: c_kraytdragon.mdl
* Node: 72 KDB_BTail_09
* Type: 0x21 HEADER MESH

## Node Chunk

| Start | End   | Size | Type       | Count                    | Description      |
|-------|-------|------|------------|--------------------------|------------------|
| 7354f | 73551 |    2 | word       | 1                        | Node Type        |
| 73551 | 7359f |   78 | NodeHeader | 1                        | Node Header      |
| 7359f | 736f3 |  340 | MeshHeader | 1                        | MeshHeader       |
| 736f3 | 73ab3 |  960 | Face       | MeshHeader.faces_count   | MeshHeader.faces_offset: face list |
| 73ab3 | 73ab7 |    4 | dword      | 1                        | MeshHeader.vertex_count_offset: list of vertex counts in vertex array |
| 73ab7 | 73eef | 1080 | Vector     | MeshHeader.vertex_count  | MeshHeader.vertex_coordinates_offset: float x,y,z for each vertex |
| 73eef | 73ee3 |    4 | dword      | 1                        | MeshHeader.vertex_offset_offset: list of offsets for vertex array |
| 73ee3 | 73ef7 |    4 | dword      | 1                        | ??? 0x11A (282) |
| 73ef7 | 73fab |  180 | ??         | MeshHeader.vertex_offset_count[0] | MeshHeader.vertex_offset_offset[0]: (30 faces, 3 vetices each, 2 bytes each. Index into vertex array)
| 73fab | 73faf |    4 | dword      | NodeHeader.child_count   | child offsets list |
| 73faf | ...   | ...  | dword      | 1                        | first child node offset |
| 74b33 |       |      |            |                          | controller offset (5 controller, each 0x10 bytes?) |
| 74b83 |       |      |            |                          | controller data start (controller data count: 17) |

Note: the controller structure is not directly adjected to the node. Maybe these controllers are shared between multiple nodes.


## NodeHeader

## MeshHeader

## Face

| Name            | Type  | Count | Description      |
|-----------------|-------|-------|-----------|
| plane_normal    | float |   3   | plane normal |
| plane_distance  | float |   1   | plane distance |
| surface         | dword |   1   |  surface flag? |
| adjected_faces  | word  |   3   | index of adjected faces |
| vertices        | word  |   3   | index into vertex buffer from MeshHeader.vertex_coordinates_offset |

## Vector
| Name | Type  | Count | Description  |
|------|-------|-------|--------------|
| x    | float |   1   | x coordinate |
| y    | float |   1   | x coordinate |
| z    | float |   1   | x coordinate |
