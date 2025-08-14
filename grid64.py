import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
import json
from PIL import Image, ImageDraw

class PixelArtEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Pixel Art Editor")
        self.root.geometry("1100x1000")
        
        # Grid settings
        self.grid_width = 64
        self.grid_height = 64
        self.pixel_size = 14
        
        # Current color
        self.current_color = "#000000"
        
        # Grid data - stores color for each pixel
        self.grid_data = {}
        
        # Drawing mode
        self.is_drawing = False
        self.is_erasing = False  # Added flag to track erasing state

        self.setup_ui()
        self.create_grid()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control panel
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        
        # Color selection
        color_frame = ttk.Frame(control_frame)
        color_frame.pack(side=tk.LEFT)
        
        ttk.Label(color_frame, text="Current Color:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.color_display = tk.Frame(color_frame, width=30, height=30, 
                                    bg=self.current_color, relief=tk.RAISED, bd=2)
        self.color_display.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(color_frame, text="Choose Color", 
                  command=self.choose_color).pack(side=tk.LEFT, padx=(0, 20))
        
        # Quick colors
        quick_colors = ["#000000", "#FFFFFF", "#FF0000", "#00FF00", "#0000FF", 
                       "#FFFF00", "#FF00FF", "#00FFFF", "#FFA500", "#800080"]
        
        for color in quick_colors:
            color_btn = tk.Button(color_frame, width=2, height=1, bg=color,
                                command=lambda c=color: self.set_color(c))
            color_btn.pack(side=tk.LEFT, padx=1)
        
        # Tools
        tools_frame = ttk.Frame(control_frame)
        tools_frame.pack(side=tk.RIGHT)
        
        ttk.Button(tools_frame, text="Clear All", 
                  command=self.clear_grid).pack(side=tk.LEFT, padx=5)
        ttk.Button(tools_frame, text="Save JSON", 
                  command=self.save_art).pack(side=tk.LEFT, padx=5)
        ttk.Button(tools_frame, text="Save PNG", 
                  command=self.export_png).pack(side=tk.LEFT, padx=5)
        ttk.Button(tools_frame, text="Save JPEG", 
                  command=self.export_jpeg).pack(side=tk.LEFT, padx=5)
        ttk.Button(tools_frame, text="Load", 
                  command=self.load_art).pack(side=tk.LEFT, padx=5)
        
        # Grid size controls
        size_frame = ttk.Frame(control_frame)
        size_frame.pack(side=tk.RIGHT, padx=(20, 0))
        
        ttk.Label(size_frame, text="Grid Size:").pack(side=tk.LEFT)
        
        size_var = tk.StringVar(value=f"{self.grid_width}x{self.grid_height}")
        size_combo = ttk.Combobox(size_frame, textvariable=size_var, width=8,
                                 values=["16x16", "32x32", "64x64", "128x128"])
        size_combo.pack(side=tk.LEFT, padx=5)
        size_combo.bind("<<ComboboxSelected>>", self.change_grid_size)
        
        # Canvas frame
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollable canvas
        self.canvas = tk.Canvas(canvas_frame, bg="white", scrollregion=(0, 0, 1000, 1000))
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and canvas
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.draw_pixel)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drawing)
        
        # Modified right-click events for hold-to-erase
        self.canvas.bind("<Button-3>", self.start_erasing)        # Right mouse down
        self.canvas.bind("<B3-Motion>", self.erase_pixel_motion)  # Right mouse drag
        self.canvas.bind("<ButtonRelease-3>", self.stop_erasing)  # Right mouse up
        
    def create_grid(self):
        """Create the pixel grid"""
        self.canvas.delete("all")
        self.grid_data = {}
        
        canvas_width = self.grid_width * self.pixel_size
        canvas_height = self.grid_height * self.pixel_size
        
        # Update scroll region
        self.canvas.configure(scrollregion=(0, 0, canvas_width + 50, canvas_height + 50))
        
        # Create grid lines
        for i in range(self.grid_width + 1):
            x = i * self.pixel_size
            self.canvas.create_line(x, 0, x, canvas_height, fill="lightgray", tags="grid")
            
        for i in range(self.grid_height + 1):
            y = i * self.pixel_size
            self.canvas.create_line(0, y, canvas_width, y, fill="lightgray", tags="grid")
    
    def get_grid_position(self, x, y):
        """Convert canvas coordinates to grid coordinates"""
        canvas_x = self.canvas.canvasx(x)
        canvas_y = self.canvas.canvasy(y)
        
        grid_x = int(canvas_x // self.pixel_size)
        grid_y = int(canvas_y // self.pixel_size)
        
        if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
            return grid_x, grid_y
        return None, None
    
    def draw_pixel_at(self, grid_x, grid_y, color=None):
        """Draw a pixel at the given grid coordinates"""
        if color is None:
            color = self.current_color
            
        x1 = grid_x * self.pixel_size
        y1 = grid_y * self.pixel_size
        x2 = x1 + self.pixel_size
        y2 = y1 + self.pixel_size
        
        # Remove existing pixel
        pixel_tag = f"pixel_{grid_x}_{grid_y}"
        self.canvas.delete(pixel_tag)
        
        # Draw new pixel
        if color != "white":  # Don't draw white pixels (transparent)
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, 
                                       outline=color, tags=pixel_tag)
            self.grid_data[(grid_x, grid_y)] = color
        elif (grid_x, grid_y) in self.grid_data:
            del self.grid_data[(grid_x, grid_y)]
    
    def start_drawing(self, event):
        """Start drawing mode"""
        self.is_drawing = True
        self.draw_pixel(event)
    
    def draw_pixel(self, event):
        """Draw pixel at mouse position"""
        if self.is_drawing:
            grid_x, grid_y = self.get_grid_position(event.x, event.y)
            if grid_x is not None:
                self.draw_pixel_at(grid_x, grid_y)
    
    def stop_drawing(self, event):
        """Stop drawing mode"""
        self.is_drawing = False
    
    def start_erasing(self, event):
        """Start erasing mode with right-click"""
        self.is_erasing = True
        self.erase_pixel_at_position(event)

    def erase_pixel_motion(self, event):
        """Erase pixel while dragging with right mouse button"""
        if self.is_erasing:
            self.erase_pixel_at_position(event)

    def erase_pixel_at_position(self, event):
        """Erase pixel at the given event position"""
        grid_x, grid_y = self.get_grid_position(event.x, event.y)
        if grid_x is not None:
            self.draw_pixel_at(grid_x, grid_y, "white")

    def stop_erasing(self, event):
        """Stop erasing mode"""
        self.is_erasing = False

    def choose_color(self):
        """Open color chooser dialog"""
        color = colorchooser.askcolor(color=self.current_color)[1]
        if color:
            self.set_color(color)
    
    def set_color(self, color):
        """Set the current drawing color"""
        self.current_color = color
        self.color_display.config(bg=color)
    
    def clear_grid(self):
        """Clear all pixels"""
        if messagebox.askyesno("Clear Grid", "Are you sure you want to clear all pixels?"):
            self.grid_data = {}
            self.canvas.delete("pixel")
            # Recreate grid to ensure it's on top
            for item in self.canvas.find_withtag("grid"):
                self.canvas.tag_raise(item)
    
    def change_grid_size(self, event=None):
        """Change the grid size"""
        size_str = event.widget.get()
        try:
            width, height = map(int, size_str.split('x'))
            self.grid_width = width
            self.grid_height = height
            self.create_grid()
        except ValueError:
            messagebox.showerror("Invalid Size", "Please enter size in format WIDTHxHEIGHT")
    
    def create_image(self, scale_factor=1):
        """Create a PIL Image from the grid data"""
        # Calculate image size
        img_width = self.grid_width * scale_factor
        img_height = self.grid_height * scale_factor
        
        # Create image with white background
        image = Image.new('RGB', (img_width, img_height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Draw each pixel
        for (grid_x, grid_y), color in self.grid_data.items():
            # Calculate pixel position in the image
            x1 = grid_x * scale_factor
            y1 = grid_y * scale_factor
            x2 = x1 + scale_factor
            y2 = y1 + scale_factor
            
            # Draw the pixel (rectangle)
            draw.rectangle([x1, y1, x2-1, y2-1], fill=color)
        
        return image
    
    def export_png(self):
        """Export the pixel art as PNG"""
        if not self.grid_data:
            messagebox.showwarning("Nothing to Export", "The canvas is empty!")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # Ask for scale factor
                scale_dialog = ScaleDialog(self.root)
                self.root.wait_window(scale_dialog.dialog)
                scale_factor = scale_dialog.result
                
                if scale_factor:
                    image = self.create_image(scale_factor)
                    image.save(filename, 'PNG')
                    messagebox.showinfo("Success", f"PNG exported successfully!\nSize: {image.width}x{image.height}")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Could not export PNG: {str(e)}")
    
    def export_jpeg(self):
        """Export the pixel art as JPEG"""
        if not self.grid_data:
            messagebox.showwarning("Nothing to Export", "The canvas is empty!")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG files", "*.jpg"), ("JPEG files", "*.jpeg"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # Ask for scale factor
                scale_dialog = ScaleDialog(self.root)
                self.root.wait_window(scale_dialog.dialog)
                scale_factor = scale_dialog.result
                
                if scale_factor:
                    image = self.create_image(scale_factor)
                    # Convert to RGB (JPEG doesn't support transparency)
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    image.save(filename, 'JPEG', quality=95)
                    messagebox.showinfo("Success", f"JPEG exported successfully!\nSize: {image.width}x{image.height}")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Could not export JPEG: {str(e)}")
    
    def save_art(self):
        """Save the pixel art to a JSON file"""
        if not self.grid_data:
            messagebox.showwarning("Nothing to Save", "The canvas is empty!")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                save_data = {
                    'grid_width': self.grid_width,
                    'grid_height': self.grid_height,
                    'pixel_size': self.pixel_size,
                    'pixels': {f"{x},{y}": color for (x, y), color in self.grid_data.items()}
                }
                
                with open(filename, 'w') as f:
                    json.dump(save_data, f, indent=2)
                    
                messagebox.showinfo("Success", "Pixel art saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file: {str(e)}")
    
    def load_art(self):
        """Load pixel art from a JSON file"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    save_data = json.load(f)
                
                # Update grid settings
                self.grid_width = save_data.get('grid_width', 32)
                self.grid_height = save_data.get('grid_height', 32)
                self.pixel_size = save_data.get('pixel_size', 12)
                
                # Recreate grid
                self.create_grid()
                
                # Load pixels
                pixels = save_data.get('pixels', {})
                for pos_str, color in pixels.items():
                    x, y = map(int, pos_str.split(','))
                    self.draw_pixel_at(x, y, color)
                
                messagebox.showinfo("Success", "Pixel art loaded successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not load file: {str(e)}")

class ScaleDialog:
    """Dialog to ask user for export scale factor"""
    def __init__(self, parent):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Export Scale")
        self.dialog.geometry("300x250")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Content
        ttk.Label(self.dialog, text="Choose export scale:").pack(pady=10)
        ttk.Label(self.dialog, text="(Higher scale = larger image)").pack(pady=(0, 10))
        
        self.scale_var = tk.IntVar(value=10)
        
        scale_frame = ttk.Frame(self.dialog)
        scale_frame.pack(pady=10)
        
        for scale in [1, 5, 10, 20, 50]:
            ttk.Radiobutton(scale_frame, text=f"{scale}x", variable=self.scale_var, 
                           value=scale).pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter and Escape keys
        self.dialog.bind('<Return>', lambda e: self.ok_clicked())
        self.dialog.bind('<Escape>', lambda e: self.cancel_clicked())
        
    def ok_clicked(self):
        self.result = self.scale_var.get()
        self.dialog.destroy()
        
    def cancel_clicked(self):
        self.result = None
        self.dialog.destroy()

def main():
    root = tk.Tk()
    app = PixelArtEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
