import glfw 
import OpenGL.GL as gl
import imgui
from imgui.integrations.glfw import GlfwRenderer 

class Gui(object):
    def __init__(self, window_name = "", window_width = 800, window_height = 600, is_resizeable = False) -> None:
        self.window_name = window_name
        self.window_width = window_width
        self.window_height = window_height
        self.is_resizeable = is_resizeable
        self.fonts_map = {} 
        self.window_stop = True

    def glfw_init(self):
        window_name = self.window_name

        if not glfw.init():
            print("Could not initialize OpenGL context")
            exit(1)

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE) 
        
        window = glfw.create_window(int(self.window_width), int(self.window_height), window_name, None, None)    
        monitor = glfw.get_monitors()[0]
        mode = glfw.get_video_mode(monitor)  
        glfw.set_window_attrib(window, glfw.RESIZABLE, self.is_resizeable)
        glfw.set_window_pos(window, int((mode.size.width - self.window_width) / 2), int((mode.size.height - self.window_height) / 2))
        glfw.make_context_current(window)

        if not window:
            glfw.terminate()
            print("Could not initialize Window")
            exit(1)

        return window

    def render_frame(self, impl, window, jb, font):
        glfw.wait_events_timeout(0.1)
        impl.process_inputs()
        imgui.new_frame()

        gl.glClearColor(0.1, 0.1, 0.1, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        if font is not None:
            imgui.push_font(font)
        self.frame_commands()
        if font is not None:
            imgui.pop_font()

        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    def frame_commands(self, show_test_window = False): 
        if show_test_window:
            imgui.show_test_window() 

    def display_frames(self, fonts_map : dict = {}):
        path_to_font = None
        imgui.create_context()
        self.window = self.glfw_init()

        self.impl = GlfwRenderer(self.window)

        io = imgui.get_io()
        jb = io.fonts.add_font_from_file_ttf(path_to_font, 30) if path_to_font is not None else None
        for key, value in fonts_map.items():
            font_size = value['font-size']
            font_path = value['font-path']
            font_obj = io.fonts.add_font_from_file_ttf(font_path, font_size)
            value['font-obj'] = font_obj
        
        self.fonts_map = fonts_map
        self.impl.refresh_font_texture() 
        
        while not glfw.window_should_close(self.window) and self.window_stop:   
            self.render_frame(self.impl, self.window, jb, path_to_font)   
            self.window_width, self.window_height = glfw.get_window_size(self.window)
             
        self.impl.shutdown()
        glfw.terminate()  
        return False
