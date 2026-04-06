from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

app = Ursina()

# load all assets
textures = {
    1: load_texture("Assets/Textures/Grass.png"),
    2: load_texture("Assets/Textures/Dirt.png"),
    3: load_texture("Assets/Textures/Brick.png"),
    4: load_texture("Assets/Textures/Wood.png"),
    5: load_texture("Assets/Textures/Stone.png"),
}

sky_bg = load_texture("Assets/Textures/Sky.png")
build_sound = Audio("Assets/SFX/Build_Sound.wav", loop=False, autoplay=False)

block_pick = 1
CHUNK_SIZE = 8
TERRAIN_SIZE = 40
TERRAIN_HEIGHT = 5

# Store block data as a dict: (x,y,z) -> texture_id
block_data = {}
# Store chunk meshes: (cx,cz) -> Entity
chunks = {}


def get_chunk_key(x, z):
    return (int(x) // CHUNK_SIZE, int(z) // CHUNK_SIZE)


def build_chunk(cx, cz):
    """Build one combined mesh per texture in this chunk."""
    # Destroy old chunk entities
    if (cx, cz) in chunks:
        for e in chunks[(cx, cz)]:
            destroy(e)

    x_start = cx * CHUNK_SIZE
    z_start = cz * CHUNK_SIZE

    # Group blocks by texture
    by_texture = {}
    for x in range(x_start, x_start + CHUNK_SIZE):
        for z in range(z_start, z_start + CHUNK_SIZE):
            for (bx, by, bz), tex_id in block_data.items():
                if bx == x and bz == z:
                    by_texture.setdefault(tex_id, []).append((bx, by, bz))

    chunk_entities = []
    for tex_id, positions in by_texture.items():
        parent = Entity()
        for (x, y, z) in positions:
            Entity(
                parent=parent,
                position=(x, y, z),
                model="Assets/Models/Block.obj",
                origin_y=0.5,
                scale=0.5,
            )
        parent.combine()
        parent.texture = textures[tex_id]
        parent.collider = "mesh"
        chunk_entities.append(parent)

    chunks[(cx, cz)] = chunk_entities


def get_block_pos(hit):
    """From a raycast hit, find the block position in the grid."""
    target = hit.world_point - hit.normal * 0.01
    return round(target.x), round(target.y), round(target.z)


class InteractionHandler(Entity):
    """Handles block placement and destruction via raycasting."""
    def input(self, key):
        global block_pick
        if key == "left mouse down":
            hit = raycast(camera.world_position, camera.forward, distance=8)
            if hit.hit:
                bx, by, bz = get_block_pos(hit)
                # Snap normal to nearest axis
                n = hit.normal
                nx = round(n.x)
                ny = round(n.y)
                nz = round(n.z)
                px, py, pz = bx + nx, by + ny, bz + nz
                if (px, py, pz) not in block_data:
                    build_sound.play()
                    block_data[(px, py, pz)] = block_pick
                    build_chunk(*get_chunk_key(px, pz))

        elif key == "right mouse down":
            hit = raycast(camera.world_position, camera.forward, distance=8)
            if hit.hit:
                bx, by, bz = get_block_pos(hit)
                if (bx, by, bz) in block_data and by >= 0:
                    build_sound.play()
                    del block_data[(bx, by, bz)]
                    build_chunk(*get_chunk_key(bx, bz))


class Sky(Entity):
    def __init__(self):
        super().__init__(
            parent=scene,
            model="sphere",
            texture=sky_bg,
            scale=150,
            double_sided=True,
        )


class Tree(Entity):
    def __init__(self, position=(0, 0, 0)):
        super().__init__(
            parent=scene,
            position=position,
            model="Assets/Models/Lowpoly_tree_sample.obj",
            scale=(0.6, 0.6, 0.6),
            collider="mesh",
        )


def generate_trees(num_trees=7, terrain_size=TERRAIN_SIZE):
    for _ in range(num_trees):
        x = random.randint(0, terrain_size - 1)
        y = 3
        z = random.randint(0, terrain_size - 1)
        Tree(position=(x, y, z))


def generate_terrain():
    # Populate block data
    for z in range(TERRAIN_SIZE):
        for x in range(TERRAIN_SIZE):
            block_data[(x, TERRAIN_HEIGHT - 1, z)] = 1  # Grass on top
            block_data[(x, -1, z)] = 5                   # Bedrock

    # Build all chunks
    num_chunks = TERRAIN_SIZE // CHUNK_SIZE
    for cx in range(num_chunks):
        for cz in range(num_chunks):
            build_chunk(cx, cz)


def update():
    global block_pick
    for i in range(1, 6):
        if held_keys[str(i)]:
            block_pick = i
            break

    if held_keys["escape"]:
        application.quit()
    if player.y <= -5:
        player.position = (10, 10, 10)

    # Update block highlight preview (show where new block would be placed)
    hit = raycast(camera.world_position, camera.forward, distance=8)
    if hit.hit:
        bx, by, bz = get_block_pos(hit)
        n = hit.normal
        nx, ny, nz = round(n.x), round(n.y), round(n.z)
        highlight.visible = True
        highlight.position = (bx + nx, by + ny, bz + nz)
    else:
        highlight.visible = False


player = FirstPersonController(position=(1, 10, 1))
player.cursor.visible = False

highlight = Entity(
    model="Assets/Models/Block.obj",
    origin_y=0.5,
    scale=0.5,
    color=color.Color(0, 0, 1, 0.3),
    unlit=True,
)

sky = Sky()
interaction = InteractionHandler()
generate_trees()
generate_terrain()

if __name__ == "__main__":
    app.run()