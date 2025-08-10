import os
import grid32
import grid16
import grid64

# Get user input
grid = input("What pixel layout would you like to design in? (16/32/64): ")

# Convert to lowercase and check the options
if grid.lower() == "16":
    print("Loading 16x16 grid...")
    # Execute grid16 module - you can call functions from it
    # For example, if grid16 has a main() function:
    if hasattr(grid16, 'main'):
        grid16.main()
    elif hasattr(grid16, 'run'):
        grid16.run()
    else:
        # If no specific function, you might need to call a specific function
        print("grid16 module loaded but no main/run function found")
        
elif grid.lower() == "32":
    print("Loading 32x32 grid...")
    if hasattr(grid32, 'main'):
        grid32.main()
    elif hasattr(grid32, 'run'):
        grid32.run()
    else:
        print("grid32 module loaded but no main/run function found")
        
elif grid.lower() == "64":
    print("Loading 64x64 grid...")
    if hasattr(grid64, 'main'):
        grid64.main()
    elif hasattr(grid64, 'run'):
        grid64.run()
    else:
        print("grid64 module loaded but no main/run function found")
        
else:
    print("Invalid option. Please choose 16, 32, or 64.")