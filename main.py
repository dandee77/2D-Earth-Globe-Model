from pyray import *
from raylib import ffi

vertex_shader_code = """
#version 330

in vec3 vertexPosition;
in vec2 vertexTexCoord;

uniform mat4 mvp;

out vec2 fragTexCoord;

void main() {
    fragTexCoord = vertexTexCoord;
    gl_Position = mvp * vec4(vertexPosition, 1.0);
}
"""

fragment_shader_code = """
#version 330

const float PI = 3.14159265359;

uniform vec2 rotation; 
uniform vec2 resolution;
uniform sampler2D texture0;

in vec2 fragTexCoord;

vec2 SphericalProjection(vec2 uv, vec2 rotation) {
    float x = uv.x * 2.0 - 1.0;
    float y = uv.y * 2.0 - 1.0;
    
    float longitude = atan(x, sqrt(1.0 - x*x - y*y)) + rotation.x;
    float latitude = asin(y) + rotation.y;
    
    return vec2(longitude / (2.0 * PI), (latitude / PI) + 0.5);
}

void main() {
    vec2 uv = fragTexCoord;
    vec2 sphericalUV = SphericalProjection(uv, rotation);
    vec4 color = texture(texture0, sphericalUV);
    gl_FragColor = color;   
}
"""

class ResourceManager:

    textures = {} #to be fixed

    def __load__(self):
        pass

    def add_texture(self, name, path):
        self.textures[name] = load_texture(path.encode())

    def __unload__(self):
        for texture in self.textures.values():
            unload_texture(texture)
        self.textures.clear()

class Window:
    def __init__(self, width, height, title):
        set_config_flags(ConfigFlags.FLAG_VSYNC_HINT)
        init_window(width, height, title.encode())
        #set_target_fps(60) #if you want to limit the frame rate given by the gpu
        self.res = ResourceManager()
        self.res.add_texture("map", "res/map.png")
        self.renderer = load_render_texture(self.res.textures["map"].width, self.res.textures["map"].height)
        set_texture_filter(self.renderer.texture, TextureFilter.TEXTURE_FILTER_BILINEAR)
        self.camera = Camera2D(Vector2(get_screen_width()/2, get_screen_height()/2), Vector2(get_screen_width()/2, get_screen_height()/2), 0, 1.0)
        self.shader = load_shader_from_memory(vertex_shader_code.encode(), fragment_shader_code.encode())

        self.rot = Vector2(0, 0)
        self.update_shader_values()
        resolution = (get_screen_width(), get_screen_height())
        resolution_ptr = ffi.new("float[2]",  resolution)
        set_shader_value(self.shader, get_shader_location(self.shader, b"resolution"), resolution_ptr, ShaderUniformDataType.SHADER_UNIFORM_VEC2)

    def update_shader_values(self):
        rotation = [self.rot.x, self.rot.y]
        rotation_ptr = ffi.new("float[2]", rotation)
        set_shader_value(self.shader, get_shader_location(self.shader, b"rotation"), rotation_ptr, ShaderUniformDataType.SHADER_UNIFORM_VEC2)

    def run(self):
        source_rect = Rectangle(0, 0, self.res.textures["map"].width, self.res.textures["map"].height)
        dest_rect = Rectangle(0, 0, self.res.textures["map"].width, self.res.textures["map"].height)
        origin = Vector2(0, 0)
        
        while not window_should_close():
            if is_mouse_button_down(MouseButton.MOUSE_BUTTON_LEFT):
                delta = get_mouse_delta()
                self.rot.x += delta.x * -0.008 / self.camera.zoom
                self.rot.y += delta.y * 0.008 / self.camera.zoom
                if self.camera.zoom != 1.0: 
                    self.rot.y = clamp(self.rot.y, -self.camera.zoom / 2.5, self.camera.zoom / 2.5)
                else:
                    self.rot.y = clamp(self.rot.y, 0, 0)
                self.update_shader_values()
                
            mouse_wheel_move = get_mouse_wheel_move()
            if mouse_wheel_move is not None:
                self.camera.zoom += mouse_wheel_move * 0.1  
                self.camera.zoom = clamp(self.camera.zoom, 1.0, 5.0)  

            begin_texture_mode(self.renderer)
            clear_background(DARKBLUE)
            draw_texture_pro(self.res.textures["map"], source_rect, dest_rect, origin, 0, WHITE)
            end_texture_mode()

            begin_drawing()
            clear_background(DARKBLUE)
            begin_shader_mode(self.shader)
            begin_mode_2d(self.camera)
            draw_texture_pro(self.renderer.texture, Rectangle(0, 0, self.renderer.texture.width, -self.renderer.texture.height), Rectangle(0, 0, 500, 450), origin, 0, WHITE)
            end_mode_2d()
            end_shader_mode()
            draw_fps(10, 10)
            end_drawing()

    def __del__(self):
        close_window()
        del self.res
        unload_render_texture(self.renderer)
        unload_shader(self.shader)


def main():
    window = Window(500, 450, "wowers")
    window.run()
    del window

main()  