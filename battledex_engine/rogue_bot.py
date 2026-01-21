from .roguescript.vm import VirtualMachine
from .tetris_engine import TetrisEngine

class RogueBot:
    def __init__(self, engine: TetrisEngine):
        self.engine = engine
        self.vm = VirtualMachine()
        self._setup_native_functions()

    def _setup_native_functions(self):
        self.vm._define_native("move_left", lambda args: self.engine.submit_action("move_left"))
        self.vm._define_native("move_right", lambda args: self.engine.submit_action("move_right"))
        self.vm._define_native("move_down", lambda args: self.engine.submit_action("move_down"))
        self.vm._define_native("rotate_cw", lambda args: self.engine.submit_action("rotate_cw"))
        self.vm._define_native("rotate_ccw", lambda args: self.engine.submit_action("rotate_ccw"))
        self.vm._define_native("hard_drop", lambda args: self.engine.submit_action("hard_drop"))
        self.vm._define_native("hold", lambda args: self.engine.submit_action("hold"))
        
        # Data access
        self.vm._define_native("get_piece_x", lambda args: self.engine.state.current_piece.x if self.engine.state.current_piece else -1)
        self.vm._define_native("get_piece_y", lambda args: self.engine.state.current_piece.y if self.engine.state.current_piece else -1)
        self.vm._define_native("get_piece_shape", lambda args: self.engine.state.current_piece.shape if self.engine.state.current_piece else "")
        
        # Simple grid check: is_occupied(x, y)
        def is_occupied(args):
            if len(args) < 2: return True
            x, y = int(args[0]), int(args[1])
            if x < 0 or x >= 10 or y < 0 or y >= 40: return True
            return self.engine.state.grid[y][x] != 0
        
        self.vm._define_native("is_occupied", is_occupied)

    def run_script(self, source: str):
        """Runs the bot script. This might be called once per frame or once per 'thought'."""
        try:
            self.vm.interpret(source)
        except Exception as e:
            print(f"Bot Script Error: {e}")

    def execute_function(self, func_name: str):
        """If the script defines a function (e.g. 'on_tick'), we can call it specifically."""
        # Note: The current VM implementation of 'interpret' runs the whole script.
        # To call a specific function, we might need to look it up in self.vm.globals
        if func_name in self.vm.globals:
            func = self.vm.globals[func_name]
            self.vm.push(func)
            self.vm._call(func, 0)
            self.vm.run()
