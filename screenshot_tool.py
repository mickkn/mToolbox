
import argparse
import os
import time

import mss
from PIL import Image
from pynput import mouse, keyboard


def parser() -> argparse.Namespace:
    """Parser function to get all the arguments

    Returns:
        Argument parser
    """

    description = "Take screenshot of the screen, using mouse and keyboard events. Esc to exit."

    # Construct the argument parse and parse the arguments
    arguments = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=description)
    arguments.add_argument("-o", "--output", type=str, default="output", help="Output folder path")
    arguments.add_argument("-d", "--dual", action='store_true', help="Dual mode, taking 2 screenshots")
    print('\n' + str(arguments.parse_args()) + '\n')

    return arguments.parse_args()


class ScreenShotTool:

    def __init__(self, args: argparse.Namespace):

        self.output_folder = f"{args.output}_{time.time()}"
        self.dual_mode = args.dual

        self.counter = 1

        self.mouse_move = mouse.Listener(on_move=self.on_move)
        self.mouse_click = mouse.Listener(on_click=self.on_click)
        self.keyboard = keyboard.Listener(on_press=self.on_press)
        self.mouse_move.start()
        self.mouse_click.start()
        self.keyboard.start()

        self.region_start = (0, 0)
        all_monitor_width = mss.mss().monitors[0].get("width")
        all_monitor_height = mss.mss().monitors[0].get("height")
        self.region_end = (all_monitor_width, all_monitor_height)
        self.region_selected = False

        self.region2_start = (0, 0)
        self.region2_end = (all_monitor_width, all_monitor_height)
        self.region2_selected = False

        # Get the active window
        self.mouse_move.join()
        self.mouse_click.join()
        self.keyboard.join()

    @staticmethod
    def on_move(x, y):
        pass
        #print(f"Mouse moved to ({x}, {y})")

    def on_click(self, x, y, button, pressed):
        # Early return if region is selected
        if (self.region_selected and not self.dual_mode) or (self.region2_selected and self.dual_mode):
            return

        # Decide which region to process
        if not self.region_selected:
            self.process_region_selection("Region 1", "region_start", "region_end", pressed, x, y, button)
            self.region_selected = not pressed and button == mouse.Button.left  # Set flag once region 1 is selected
        elif self.dual_mode and not self.region2_selected:
            self.process_region_selection("Region 2", "region2_start", "region2_end", pressed, x, y, button)
            self.region2_selected = not pressed and button == mouse.Button.left  # Set flag once region 2 is selected

    def process_region_selection(self, region_name, start_attr, end_attr, pressed, x, y, button):
        """
        Helper function to handle region selection.
        """
        if pressed and button == mouse.Button.left:
            setattr(self, start_attr, (x, y))
            print(f"{region_name} Start: {getattr(self, start_attr)}")
        elif not pressed and button == mouse.Button.left:
            setattr(self, end_attr, (x, y))
            print(f"{region_name} End: {getattr(self, end_attr)}")

    def on_press(self, key):
        if key == keyboard.Key.space:
            print("Take Screenshot")
            self.take_region_screenshot()
        if key == keyboard.Key.esc:
            self.mouse_move.stop()
            self.mouse_click.stop()
            self.keyboard.stop()
            exit()

    def take_region_screenshot(self):
        """Take a screenshot of region between 2 coordinates on screen."""
        with mss.mss() as sct:
            # Capture first region
            self.capture_and_save(sct, self.region_start, self.region_end)

            if self.dual_mode:
                # Capture second region if in dual mode
                self.capture_and_save(sct, self.region2_start, self.region2_end)

    def capture_and_save(self, sct, start, end):
        """Helper function to capture a region and save the screenshot."""
        monitor = {
            "top": start[1],
            "left": start[0],
            "width": end[0] - start[0],
            "height": end[1] - start[1]
        }

        # Grab the screen data
        sct_img = sct.grab(monitor)

        # Convert to Image
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

        # Save the image
        os.makedirs(self.output_folder, exist_ok=True)
        img.save(f"{self.output_folder}/screenshot_{self.counter}.png")
        self.counter += 1


if __name__ == '__main__':

    try:
        tool = ScreenShotTool(parser())
    except Exception as e:
        print(e)
        exit()
