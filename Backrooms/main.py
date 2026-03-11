import os, random, math
import pygame

from panda3d.core import (
    GeomVertexFormat, GeomVertexData, GeomVertexWriter, GeomTriangles,
    Geom, GeomNode, Filename, WindowProperties, LVector3, Fog, loadPrcFileData
)
from direct.showbase.ShowBase import ShowBase


# --- Window / performance settings ---
loadPrcFileData("", "undecorated #t")
loadPrcFileData("", "window-title Backrooms")
loadPrcFileData("", "sync-video #t")
loadPrcFileData("", "clock-mode limited")
loadPrcFileData("", "clock-frame-rate 60")


class TrueBackroomsVibe(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)

        self.script_dir = os.path.dirname(os.path.abspath(__file__))

        # --- Initialize pygame audio ---
        pygame.mixer.init()

        hum_path = os.path.join(self.script_dir, "humbuzz.wav")
        step_path = os.path.join(self.script_dir, "footsteps.wav")

        # Backrooms buzz
        if os.path.exists(hum_path):
            pygame.mixer.music.load(hum_path)
            pygame.mixer.music.set_volume(0.30)
            pygame.mixer.music.play(-1)
        else:
            print("Sound file not found:", hum_path)

        # Quiet footsteps
        if os.path.exists(step_path):
            self.footstep_sound = pygame.mixer.Sound(step_path)
            self.footstep_sound.set_volume(0.70)  # VERY quiet
            self.step_channel = pygame.mixer.Channel(1)
        else:
            self.footstep_sound = None

        # --- Window setup ---
        res_x = self.pipe.get_display_width()
        res_y = self.pipe.get_display_height()

        props = WindowProperties()
        props.set_size(res_x, res_y)
        props.set_origin(0, 0)
        props.set_cursor_hidden(True)
        props.set_mouse_mode(WindowProperties.M_relative)
        self.win.request_properties(props)

        self.camLens.set_fov(90)
        self.disable_mouse()

        # --- Fog / atmosphere ---
        fog_color = (0.12, 0.13, 0.05)
        self.set_background_color(*fog_color)

        self.my_fog = Fog("BackroomsFog")
        self.my_fog.set_color(*fog_color)
        self.my_fog.set_exp_density(0.02)
        render.set_fog(self.my_fog)

        # --- Texture loader ---
        def load_t(name):
            path = os.path.join(self.script_dir, name)
            if os.path.exists(path):
                return loader.load_texture(Filename.from_os_specific(path))
            return None

        self.wall_tex = load_t("walls.png")
        self.ceil_tex = load_t("celing.png")
        self.floor_tex = load_t("floor.png")

        # --- World settings ---
        self.chunk_size = 8
        self.view_dist = 3
        self.chunks = {}
        self.seed = 54321

        self.camera.set_pos(0.5, 0.5, 2.5)

        # --- Controls ---
        self.keys = {"w":0,"s":0,"a":0,"d":0}

        def set_k(k,v):
            self.keys[k] = v

        for k in self.keys:
            self.accept(k, set_k, [k, 1])
            self.accept(k+"-up", set_k, [k, 0])

        self.accept("escape", exit)

        self.taskMgr.add(self.update, "update")


    # --- Cell generator ---
    def get_cell_type(self, x, y):
        rng = random.Random(
            f"{self.seed}_{int(math.floor(x/4))}_{int(math.floor(y/4))}"
        )
        return 1 if rng.random() > 0.82 else 0


    # --- Chunk builder ---
    def generate_chunk(self, cx, cy):

        chunk_node = render.attach_new_node(f"chunk_{cx}_{cy}")

        for ty in range(self.chunk_size):
            for tx in range(self.chunk_size):

                wx = cx*self.chunk_size + tx
                wy = cy*self.chunk_size + ty

                self.add_plane(wx, wy, 0.0, "floor", chunk_node, False)

                is_light = (wx % 4 == 0 and wy % 4 == 0)

                self.add_plane(wx, wy, 5.0, "ceiling", chunk_node, is_light)

                if self.get_cell_type(wx, wy) == 1:
                    self.add_block(wx, wy, 5.0, chunk_node)

        chunk_node.flatten_medium()

        return chunk_node


    # --- Wall block ---
    def add_block(self, x, y, h, parent):

        v_data = GeomVertexData(
            "wall",
            GeomVertexFormat.get_v3t2(),
            Geom.UH_static
        )

        vw = GeomVertexWriter(v_data, "vertex")
        tw = GeomVertexWriter(v_data, "texcoord")

        def side(p1,p2,p3,p4):
            for p in [p1,p2,p3,p4]:
                vw.add_data3(*p)

            tw.add_data2(0,0)
            tw.add_data2(1,0)
            tw.add_data2(1,5)
            tw.add_data2(0,5)

        side((x,y,0),(x+1,y,0),(x+1,y,h),(x,y,h))
        side((x+1,y,0),(x+1,y+1,0),(x+1,y+1,h),(x+1,y,h))
        side((x+1,y+1,0),(x,y+1,0),(x,y+1,h),(x+1,y+1,h))
        side((x,y+1,0),(x,y,0),(x,y,h),(x,y+1,h))

        self.finalize(v_data, 16, parent, "wall", False)


    # --- Floor / ceiling ---
    def add_plane(self, x, y, z, p_type, parent, is_light):

        v_data = GeomVertexData(
            "plane",
            GeomVertexFormat.get_v3t2(),
            Geom.UH_static
        )

        vw = GeomVertexWriter(v_data, "vertex")
        tw = GeomVertexWriter(v_data, "texcoord")

        for c in [(x,y,z),(x+1,y,z),(x+1,y+1,z),(x,y+1,z)]:
            vw.add_data3(*c)

        for t in [(0,0),(1,0),(1,1),(0,1)]:
            tw.add_data2(*t)

        self.finalize(v_data, 4, parent, p_type, is_light)


    # --- Geometry builder ---
    def finalize(self, v_data, count, parent, m_type, is_light):

        tris = GeomTriangles(Geom.UH_static)

        for i in range(0, count, 4):
            tris.add_vertices(i,i+1,i+2)
            tris.add_vertices(i,i+2,i+3)

        geom = Geom(v_data)
        geom.add_primitive(tris)

        node = GeomNode("mesh")
        node.add_geom(geom)

        np = parent.attach_new_node(node)

        np.set_two_sided(True)

        if is_light:

            np.set_color(4.0,3.8,1.0,1)
            np.set_light_off()

        elif m_type == "wall":

            if self.wall_tex:
                np.set_texture(self.wall_tex)

        elif m_type == "floor":

            if self.floor_tex:
                np.set_texture(self.floor_tex)

            np.set_color_scale(0.4,0.4,0.4,1)

        else:

            if self.ceil_tex:
                np.set_texture(self.ceil_tex)

            np.set_color_scale(1.2,1.2,0.6,1)


    # --- Game update loop ---
    def update(self, task):

        cx = int(self.camera.get_x() // self.chunk_size)
        cy = int(self.camera.get_y() // self.chunk_size)

        built = False

        for dy in range(-self.view_dist, self.view_dist + 1):
            for dx in range(-self.view_dist, self.view_dist + 1):

                pos = (cx + dx, cy + dy)

                if pos not in self.chunks and not built:

                    self.chunks[pos] = self.generate_chunk(*pos)
                    built = True

        to_del = [
            p for p in self.chunks
            if abs(p[0]-cx) > self.view_dist
            or abs(p[1]-cy) > self.view_dist
        ]

        for p in to_del:
            self.chunks[p].remove_node()
            del self.chunks[p]

        dt = globalClock.get_dt()

        if self.mouseWatcherNode.has_mouse():

            mw = self.mouseWatcherNode

            self.camera.set_h(
                self.camera.get_h() - mw.get_mouse_x()*100
            )

            self.camera.set_p(
                max(-85,
                    min(85,
                        self.camera.get_p()+mw.get_mouse_y()*100
                    )
                )
            )

            self.win.move_pointer(
                0,
                self.win.get_x_size()//2,
                self.win.get_y_size()//2
            )

        move = LVector3(0,0,0)

        if self.keys["w"]:
            move += LVector3.forward()

        if self.keys["s"]:
            move -= LVector3.forward()

        if self.keys["a"]:
            move -= LVector3.right()

        if self.keys["d"]:
            move += LVector3.right()

        move = render.get_relative_vector(self.camera, move)
        move.z = 0

        moving = move.length() > 0

        if self.footstep_sound:

            if moving:
                if not self.step_channel.get_busy():
                    self.step_channel.play(self.footstep_sound, loops=-1)

            else:
                self.step_channel.stop()   # stops immediately

        if move.length() > 0:

            new_pos = (
                self.camera.get_pos()
                + move.normalized() * 7.0 * dt
            )

            buffer = 0.3
            can_move = True

            for bx in [-buffer, buffer]:
                for by in [-buffer, buffer]:

                    if self.get_cell_type(
                        new_pos.x + bx,
                        new_pos.y + by
                    ) == 1:

                        can_move = False
                        break

            if can_move:
                self.camera.set_pos(new_pos)

        return task.cont


app = TrueBackroomsVibe()
app.run()