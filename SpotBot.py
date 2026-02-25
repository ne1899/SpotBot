from ij import IJ, ImagePlus, WindowManager
from ij.plugin import Duplicator
from ij.plugin.filter import ParticleAnalyzer
from ij.measure import ResultsTable, Measurements
from ij.plugin.frame import RoiManager
from ij.gui import NonBlockingGenericDialog, Overlay
from java.lang import Double
from java.awt.event import AdjustmentListener, MouseAdapter, KeyAdapter, KeyEvent, ActionEvent
from java.awt import Color

# ==================== CONFIGURATION ====================
SPOT_MIN_SIZE = 1000
SPOT_MAX_SIZE = Double.POSITIVE_INFINITY
SPOT_MIN_CIRCULARITY = 0.0
SPOT_MAX_CIRCULARITY = 1.0

LEAF_MIN_SIZE = 10000
LEAF_MAX_SIZE = Double.POSITIVE_INFINITY
LEAF_THRESHOLD_METHOD = "Triangle"

THRESHOLD_MIN = 20
THRESHOLD_MAX = 255
THRESHOLD_START = 50

SIZE_MIN = 100
SIZE_MAX = 100000
SIZE_START_MIN = 3000

imp = IJ.getImage()
current_threshold = [THRESHOLD_START]
current_size_min = [SIZE_START_MIN]

SPOT_MANUAL_THRESHOLD = THRESHOLD_START
SPOT_MANUAL_MIN_SIZE = SIZE_START_MIN

# ==================== FUNCTIONS ====================

import math
from ij.gui import OvalRoi, TextRoi
from java.awt import Font

last_dialog_location = [None]  # Remembers where user dragged the dialog

def setup_dialog(dialog):
    """Set dialog always-on-top and restore last position if available."""
    dialog.setAlwaysOnTop(True)
    if last_dialog_location[0] is not None:
        dialog.setLocation(last_dialog_location[0])

def show_dialog_with_space(dialog):
    """Show dialog with Space bar shortcut on canvas. Remembers dialog position for next time."""
    canvas = imp.getCanvas()
    class SpaceKey(KeyAdapter):
        def keyPressed(self, event):
            if event.getKeyCode() == KeyEvent.VK_SPACE:
                ok_event = ActionEvent(dialog, ActionEvent.ACTION_PERFORMED, "OK")
                dialog.actionPerformed(ok_event)
    listener = SpaceKey()
    canvas.addKeyListener(listener)
    canvas.requestFocusInWindow()
    dialog.showDialog()
    last_dialog_location[0] = dialog.getLocation()
    canvas.removeKeyListener(listener)

SIZE_SLIDER_MIN = 0
SIZE_SLIDER_MAX = 1000

def size_to_slider(size):
    """Convert actual size (10-50000) to slider value (0-1000) using log scale."""
    if size <= SIZE_MIN:
        return SIZE_SLIDER_MIN
    log_min = math.log10(SIZE_MIN)
    log_max = math.log10(SIZE_MAX)
    log_size = math.log10(size)
    return int((log_size - log_min) / (log_max - log_min) * SIZE_SLIDER_MAX)

def slider_to_size(slider_val):
    """Convert slider value (0-1000) to actual size (10-50000) using log scale."""
    log_min = math.log10(SIZE_MIN)
    log_max = math.log10(SIZE_MAX)
    log_size = log_min + (slider_val / float(SIZE_SLIDER_MAX)) * (log_max - log_min)
    return int(math.pow(10, log_size))

def add_leaf_labels_to_overlay(overlay, leaf_rm, num_leaves):
    """Add leaf outlines and centered labels to overlay."""
    for idx in range(num_leaves):
        leaf_roi = leaf_rm.getRoi(idx)
        leaf_roi.setStrokeColor(Color.GREEN)
        leaf_roi.setStrokeWidth(1)
        overlay.add(leaf_roi)

        # Use bounding box center
        bounds = leaf_roi.getBounds()
        center_x = bounds.x + bounds.width / 2.0
        center_y = bounds.y + bounds.height / 2.0

        text_roi = TextRoi(center_x, center_y, "Leaf " + str(idx + 1))
        text_roi.setStrokeColor(Color.YELLOW)
        text_roi.setFont(Font("SansSerif", Font.BOLD, 24))
        text_roi.setJustification(TextRoi.CENTER)
        overlay.add(text_roi)

def add_colored_spots_to_overlay(overlay, spots, clicked_spots):
    """Add spot ROIs to overlay with color based on clicked state."""
    for spot_roi in spots:
        is_clicked = any(spot_roi.contains(int(cx), int(cy)) for cx, cy in clicked_spots)
        spot_clone = spot_roi.clone()
        if is_clicked:
            spot_clone.setStrokeColor(Color.BLUE)
            spot_clone.setFillColor(Color(0, 0, 255, 150))
        else:
            spot_clone.setStrokeColor(Color.RED)
            spot_clone.setFillColor(Color(255, 0, 0, 150))
        spot_clone.setStrokeWidth(2)
        spot_clone.setName(None)
        overlay.add(spot_clone)

def detect_preview_spots(thresh, min_size):
    """
    Detect fluorescent spots in the image for real-time preview.

    Parameters
    ----------
    thresh : int
        Minimum intensity threshold (0-255)
    min_size : int
        Minimum spot size in pixels

    Returns
    -------
    list of ij.gui.Roi
        List of detected spot ROIs
    """
    temp = Duplicator().run(imp)
    if temp.getType() != ImagePlus.GRAY8:
        IJ.run(temp, "8-bit", "")
    temp.getProcessor().setThreshold(thresh, 255, temp.getProcessor().NO_LUT_UPDATE)
    IJ.run(temp, "Convert to Mask", "")
    IJ.run(temp, "Despeckle", "")
    IJ.run(temp, "Despeckle", "")
    IJ.run(temp, "Fill Holes", "")
    rm = RoiManager(False)
    pa = ParticleAnalyzer(ParticleAnalyzer.ADD_TO_MANAGER, Measurements.CENTROID, ResultsTable(),
                          min_size, SPOT_MAX_SIZE, SPOT_MIN_CIRCULARITY, SPOT_MAX_CIRCULARITY)
    pa.setRoiManager(rm)
    pa.analyze(temp)
    rois = [rm.getRoi(i) for i in range(rm.getCount())] if rm.getCount() > 0 else []
    temp.close()
    return rois

def update_preview():
    """
    Update the real-time preview overlay with detected spots.

    Updates the image overlay with yellow outlines showing all spots
    detected using current threshold parameters.
    """
    rois = detect_preview_spots(current_threshold[0], current_size_min[0])
    overlay = Overlay()
    for roi in rois:
        roi.setStrokeColor(Color.YELLOW)
        roi.setStrokeWidth(2)
        overlay.add(roi)
    imp.setOverlay(overlay)
    imp.updateAndDraw()

update_preview()

class ThresholdListener(AdjustmentListener):
    """
    Event listener for intensity threshold slider adjustments.

    Automatically updates spot detection preview when slider value changes.
    """
    def adjustmentValueChanged(self, event):
        val = int(event.getSource().getValue())
        if val != current_threshold[0]:
            current_threshold[0] = val
            update_preview()

class SizeMinListener(AdjustmentListener):
    """
    Event listener for minimum size slider adjustments.

    Automatically updates spot detection preview when slider value changes.
    """
    def adjustmentValueChanged(self, event):
        slider_val = int(event.getSource().getValue())
        actual_size = slider_to_size(slider_val)
        if actual_size != current_size_min[0]:
            current_size_min[0] = actual_size
            update_preview()

# ==================== INTERACTIVE THRESHOLD ADJUSTMENT ====================

dialog = NonBlockingGenericDialog("Adjust Spot Detection")
dialog.addSlider("Min Intensity:", THRESHOLD_MIN, THRESHOLD_MAX, current_threshold[0])
dialog.addSlider("Min Size (log scale):", SIZE_SLIDER_MIN, SIZE_SLIDER_MAX, size_to_slider(current_size_min[0]))
dialog.addMessage("Current size: " + str(current_size_min[0]) + " pixels (range: 10-50000)")
dialog.setOKLabel("Accept and Continue")

sliders = dialog.getSliders()
if sliders and len(sliders) >= 2:
    sliders.get(0).addAdjustmentListener(ThresholdListener())
    sliders.get(1).addAdjustmentListener(SizeMinListener())

setup_dialog(dialog)
dialog.showDialog()
last_dialog_location[0] = dialog.getLocation()

if dialog.wasOKed():
    SPOT_MANUAL_THRESHOLD = int(dialog.getNextNumber())
    slider_value = int(dialog.getNextNumber())
    SPOT_MANUAL_MIN_SIZE = slider_to_size(slider_value)
    imp.setOverlay(None)
else:
    imp.setOverlay(None)
    import sys
    sys.exit()

# ==================== LEAF DETECTION ====================

leaf_detector = Duplicator().run(imp)
if leaf_detector.getType() != ImagePlus.GRAY8:
    IJ.run(leaf_detector, "8-bit", "")

# Light blur to reduce noise
IJ.run(leaf_detector, "Gaussian Blur...", "sigma=2")

# Interactive threshold adjustment for leaf detection
current_leaf_threshold = [50]

def update_leaf_preview():
    """Update preview showing detected leaves with current threshold."""
    temp = Duplicator().run(leaf_detector)
    temp.getProcessor().setThreshold(current_leaf_threshold[0], 255, temp.getProcessor().NO_LUT_UPDATE)
    IJ.run(temp, "Convert to Mask", "")
    IJ.run(temp, "Fill Holes", "")

    preview_rm = RoiManager(False)
    preview_pa = ParticleAnalyzer(
        ParticleAnalyzer.ADD_TO_MANAGER | ParticleAnalyzer.SHOW_NONE,
        Measurements.CENTROID,
        ResultsTable(),
        LEAF_MIN_SIZE,
        LEAF_MAX_SIZE,
        0.0, 1.0
    )
    preview_pa.setRoiManager(preview_rm)
    preview_pa.analyze(temp)
    temp.close()

    overlay = Overlay()
    for i in range(preview_rm.getCount()):
        roi = preview_rm.getRoi(i)
        roi.setStrokeColor(Color.YELLOW)
        roi.setStrokeWidth(2)
        overlay.add(roi)
    imp.setOverlay(overlay)
    imp.updateAndDraw()

class LeafThresholdListener(AdjustmentListener):
    def adjustmentValueChanged(self, event):
        val = int(event.getSource().getValue())
        if val != current_leaf_threshold[0]:
            current_leaf_threshold[0] = val
            update_leaf_preview()

update_leaf_preview()

leaf_thresh_dialog = NonBlockingGenericDialog("Adjust Leaf Detection Threshold")
leaf_thresh_dialog.addSlider("Threshold:", 1, 255, current_leaf_threshold[0])
leaf_thresh_dialog.addMessage("Adjust until leaves are separated.\nHigher = less sensitive\nLower = more sensitive")
leaf_thresh_dialog.setOKLabel("Accept")
leaf_thresh_dialog.setCancelLabel("Cancel")

leaf_sliders = leaf_thresh_dialog.getSliders()
if leaf_sliders and len(leaf_sliders) >= 1:
    leaf_sliders.get(0).addAdjustmentListener(LeafThresholdListener())

setup_dialog(leaf_thresh_dialog)
leaf_thresh_dialog.showDialog()
last_dialog_location[0] = leaf_thresh_dialog.getLocation()

if leaf_thresh_dialog.wasCanceled():
    leaf_detector.close()
    imp.setOverlay(None)
    import sys
    sys.exit()

final_leaf_threshold = int(leaf_thresh_dialog.getNextNumber())

leaf_detector.getProcessor().setThreshold(final_leaf_threshold, 255, leaf_detector.getProcessor().NO_LUT_UPDATE)
IJ.run(leaf_detector, "Convert to Mask", "")
IJ.run(leaf_detector, "Fill Holes", "")

leaf_rm = RoiManager(False)
leaf_pa = ParticleAnalyzer(
    ParticleAnalyzer.ADD_TO_MANAGER | ParticleAnalyzer.SHOW_NONE,
    Measurements.CENTROID,
    ResultsTable(),
    LEAF_MIN_SIZE,
    LEAF_MAX_SIZE,
    0.0,
    1.0
)
leaf_pa.setRoiManager(leaf_rm)
leaf_pa.analyze(leaf_detector)

num_leaves = leaf_rm.getCount()
leaf_detector.close()

imp.setOverlay(None)
IJ.showStatus("Found " + str(num_leaves) + " leaves")

# ==================== SPOT DETECTION & ASSIGNMENT ====================

if num_leaves > 0:
    imp_copy = Duplicator().run(imp)
    if imp_copy.getType() != ImagePlus.GRAY8:
        IJ.run(imp_copy, "8-bit", "")
    imp_copy.getProcessor().setThreshold(SPOT_MANUAL_THRESHOLD, 255, imp_copy.getProcessor().NO_LUT_UPDATE)

    IJ.run(imp_copy, "Convert to Mask", "")
    IJ.run(imp_copy, "Despeckle", "")
    IJ.run(imp_copy, "Despeckle", "")
    IJ.run(imp_copy, "Fill Holes", "")

    temp_rm = RoiManager(False)
    IJ.run("Set Measurements...", "mean redirect=None decimal=3")

    temp_pa = ParticleAnalyzer(
        ParticleAnalyzer.ADD_TO_MANAGER,
        Measurements.CENTROID,
        ResultsTable(),
        SPOT_MANUAL_MIN_SIZE,
        SPOT_MAX_SIZE,
        SPOT_MIN_CIRCULARITY,
        SPOT_MAX_CIRCULARITY
    )
    temp_pa.setRoiManager(temp_rm)
    temp_pa.analyze(imp_copy)
    imp_copy.close()

    total_spots = temp_rm.getCount()

    if total_spots > 0:
        # Create list to store spots for each leaf (index 0 = unassigned spots)
        spots_by_leaf = [[] for _ in range(num_leaves + 1)]

        # Assign each spot to a leaf based on centroid location (fast direct check)
        for spot_idx in range(total_spots):
            spot_roi = temp_rm.getRoi(spot_idx)
            bounds = spot_roi.getBounds()
            cx = int(bounds.x + bounds.width / 2.0)
            cy = int(bounds.y + bounds.height / 2.0)

            # Check which leaf ROI contains this spot's centroid
            assigned = False
            for leaf_idx in range(num_leaves):
                leaf_roi = leaf_rm.getRoi(leaf_idx)
                if leaf_roi.contains(cx, cy):
                    spots_by_leaf[leaf_idx + 1].append(spot_roi)
                    assigned = True
                    break

            if not assigned:
                spots_by_leaf[0].append(spot_roi)

        ordered_spots_by_leaf = [[] for _ in range(num_leaves + 1)]

        # ==================== INTERACTIVE SPOT ORDERING ====================

        for leaf_num in range(1, num_leaves + 1):
            if len(spots_by_leaf[leaf_num]) == 0:
                continue

            imp.show()
            WindowManager.setCurrentWindow(imp.getWindow())
            imp.getWindow().toFront()

            imp.setOverlay(None)
            imp.setRoi(None)
            imp.updateAndDraw()

            # ==================== OPTIONAL: EDIT DETECTED SPOTS ====================
            # Show leaf context as overlay (non-editable)
            edit_overlay = Overlay()
            add_leaf_labels_to_overlay(edit_overlay, leaf_rm, num_leaves)
            imp.setOverlay(edit_overlay)
            imp.updateAndDraw()

            # Use a visible ROI Manager for editing
            temp_edit_rm = RoiManager.getInstance()
            if temp_edit_rm is None:
                temp_edit_rm = RoiManager()
            temp_edit_rm.reset()

            # Add all detected spots to ROI Manager
            for spot_roi in spots_by_leaf[leaf_num]:
                spot_clone = spot_roi.clone()
                temp_edit_rm.addRoi(spot_clone)

            # Show all ROIs on image with labels enabled
            temp_edit_rm.runCommand(imp, "Show All with labels")
            temp_edit_rm.runCommand("UseNames", "false")

            # Switch to selection tool so users can click and drag ROIs directly
            IJ.setTool("rectangle")

            edit_dialog = NonBlockingGenericDialog("Edit Detected Spots - Leaf " + str(leaf_num))
            edit_dialog.addMessage("Review detected spots in ROI Manager (right panel).\n\n" +
                                   "You can edit, add, or delete spots.\n\n" +
                                   "Click 'Continue' when ready to order spots.")
            edit_dialog.setOKLabel("Continue")
            edit_dialog.setCancelLabel("Cancel")
            setup_dialog(edit_dialog)
            edit_dialog.showDialog()
            last_dialog_location[0] = edit_dialog.getLocation()

            if edit_dialog.wasCanceled():
                import sys
                sys.exit()

            # Update spots list with any manual edits from ROI manager
            spots_by_leaf[leaf_num] = [temp_edit_rm.getRoi(i) for i in range(temp_edit_rm.getCount())]

            # Close ROI Manager to prevent it intercepting clicks
            temp_edit_rm.runCommand(imp, "Show None")
            temp_edit_rm.close()

            # ==================== SPOT ORDERING DISPLAY ====================
            imp.setOverlay(None)
            imp.setRoi(None)
            imp.updateAndDraw()

            # Track which spots have been clicked (for blue coloring)
            clicked_spot_indices = []

            def update_spot_overlay():
                """Rebuild overlay with clicked spots in blue, unclicked in red."""
                overlay = Overlay()
                add_leaf_labels_to_overlay(overlay, leaf_rm, num_leaves)
                for idx, spot_roi in enumerate(spots_by_leaf[leaf_num]):
                    spot_clone = spot_roi.clone()
                    if idx in clicked_spot_indices:
                        spot_clone.setStrokeColor(Color.BLUE)
                        spot_clone.setFillColor(Color(0, 0, 255, 100))
                    else:
                        spot_clone.setStrokeColor(Color.RED)
                        spot_clone.setFillColor(Color(255, 0, 0, 100))
                    spot_clone.setStrokeWidth(2)
                    spot_clone.setName(None)
                    overlay.add(spot_clone)
                imp.setOverlay(overlay)
                imp.updateAndDraw()

            # Initial overlay (all red)
            update_spot_overlay()

            # Mouse listener for real-time blue feedback
            class SpotClickListener(MouseAdapter):
                def mouseReleased(self, event):
                    canvas = imp.getCanvas()
                    click_x = canvas.offScreenX(event.getX())
                    click_y = canvas.offScreenY(event.getY())

                    # First check if click is inside any spot ROI
                    nearest_idx = -1
                    for idx, spot_roi in enumerate(spots_by_leaf[leaf_num]):
                        if spot_roi.contains(click_x, click_y):
                            nearest_idx = idx
                            break

                    # Fall back to nearest centroid within 150 pixels
                    if nearest_idx < 0:
                        min_dist = float('inf')
                        for idx, spot_roi in enumerate(spots_by_leaf[leaf_num]):
                            bounds = spot_roi.getBounds()
                            spot_cx = bounds.x + bounds.width / 2.0
                            spot_cy = bounds.y + bounds.height / 2.0
                            dist = ((click_x - spot_cx)**2 + (click_y - spot_cy)**2)**0.5
                            if dist < min_dist and dist < 150:
                                min_dist = dist
                                nearest_idx = idx

                    if nearest_idx >= 0 and nearest_idx not in clicked_spot_indices:
                        clicked_spot_indices.append(nearest_idx)
                        update_spot_overlay()
                        canvas.requestFocusInWindow()

            click_listener = SpotClickListener()
            canvas = imp.getCanvas()
            canvas.addMouseListener(click_listener)

            # Set multipoint tool for clicking
            IJ.setTool("multipoint")

            order_dialog = NonBlockingGenericDialog("Click Spots in Order - Leaf " + str(leaf_num))

            if leaf_num == 1:
                msg = "You are ordering spots for LEAF " + str(leaf_num) + ".\n\n"
                msg += "Click on each red circle in your desired measurement order.\n"
                msg += "Circles turn BLUE when clicked.\n\n"
                msg += "IMPORTANT: Only clicked spots will be measured!\n\n"
                msg += "When done clicking, press Next above."
            else:
                msg = "Leaf " + str(leaf_num)

            order_dialog.addMessage(msg)

            if leaf_num == num_leaves:
                order_dialog.setOKLabel("Done")
            else:
                order_dialog.setOKLabel("Next")

            order_dialog.setCancelLabel("Cancel")
            setup_dialog(order_dialog)
            show_dialog_with_space(order_dialog)

            # Remove mouse listener
            canvas.removeMouseListener(click_listener)

            if order_dialog.wasCanceled():
                import sys
                sys.exit()

            # Use the clicked spots (tracked by mouse listener) in order
            for idx in clicked_spot_indices:
                ordered_spots_by_leaf[leaf_num].append(spots_by_leaf[leaf_num][idx])

            imp.setRoi(None)
            imp.setOverlay(None)
            imp.updateAndDraw()

        ordered_spots_by_leaf[0] = spots_by_leaf[0][:]

        # ==================== MEASUREMENT & OUTPUT ====================

        IJ.run("Clear Results")

        display_rm = RoiManager.getInstance()
        if display_rm is None:
            display_rm = RoiManager()
        display_rm.reset()

        # Measure all ordered spots for each leaf
        for leaf_num in range(1, num_leaves + 1):
            spot_counter = 1  # Reset spot counter for each leaf
            for spot_roi in ordered_spots_by_leaf[leaf_num]:
                imp.setRoi(spot_roi)
                imp.getWindow().toFront()
                IJ.run("Measure")
                display_rm.addRoi(spot_roi)
                rt = ResultsTable.getResultsTable()
                row = rt.getCounter() - 1
                rt.setValue("Spot", row, spot_counter)
                rt.setValue("Leaf", row, leaf_num)
                spot_counter += 1

        # Measure unassigned spots (if any)
        if len(ordered_spots_by_leaf[0]) > 0:
            spot_counter = 1  # Reset for unassigned spots too
            for spot_roi in ordered_spots_by_leaf[0]:
                imp.setRoi(spot_roi)
                imp.getWindow().toFront()
                IJ.run("Measure")
                display_rm.addRoi(spot_roi)
                rt = ResultsTable.getResultsTable()
                row = rt.getCounter() - 1
                rt.setValue("Spot", row, spot_counter)
                rt.setValue("Leaf", row, 0)
                spot_counter += 1

        # Create clean results table with only Spot, Leaf, Mean
        rt = ResultsTable.getResultsTable()
        clean_rt = ResultsTable()

        for row in range(rt.getCounter()):
            clean_rt.incrementCounter()
            clean_rt.setValue("Spot", row, int(rt.getValue("Spot", row)))
            clean_rt.setValue("Leaf", row, int(rt.getValue("Leaf", row)))
            clean_rt.setValue("Mean", row, rt.getValue("Mean", row))

        clean_rt.show("Results")
        display_rm.runCommand(imp, "Show All")

        # Auto-save results to master CSV (append if exists)
        image_path = imp.getOriginalFileInfo()
        if image_path is not None and image_path.directory is not None:
            import os
            output_dir = image_path.directory
            image_name = os.path.splitext(image_path.fileName)[0]
            csv_path = os.path.join(output_dir, "SpotBot_Results.csv")  # Single master file

            # Check if file exists and append if so
            if os.path.exists(csv_path):
                # Append new data rows (no header)
                with open(csv_path, 'a') as f:
                    for row in range(clean_rt.getCounter()):
                        spot = int(clean_rt.getValue("Spot", row))
                        leaf = int(clean_rt.getValue("Leaf", row))
                        mean = clean_rt.getValue("Mean", row)
                        f.write(image_name + "," + str(spot) + "," + str(leaf) + "," + str(mean) + "\n")
                IJ.log("Results appended to: " + csv_path)
            else:
                # Write new file with header
                with open(csv_path, 'w') as f:
                    f.write("Image,Spot,Leaf,Mean\n")
                    for row in range(clean_rt.getCounter()):
                        spot = int(clean_rt.getValue("Spot", row))
                        leaf = int(clean_rt.getValue("Leaf", row))
                        mean = clean_rt.getValue("Mean", row)
                        f.write(image_name + "," + str(spot) + "," + str(leaf) + "," + str(mean) + "\n")
                IJ.log("Results saved to: " + csv_path)
        else:
            # Image path not available - ask user where to save
            from ij.io import SaveDialog
            sd = SaveDialog("Save SpotBot Results", "SpotBot_Results", ".csv")
            save_dir = sd.getDirectory()
            save_name = sd.getFileName()
            if save_dir is not None and save_name is not None:
                import os
                csv_path = os.path.join(save_dir, save_name)
                image_name = imp.getTitle().replace(".tif", "").replace(".tiff", "").replace(".png", "").replace(".jpg", "")
                if os.path.exists(csv_path):
                    with open(csv_path, 'a') as f:
                        for row in range(clean_rt.getCounter()):
                            spot = int(clean_rt.getValue("Spot", row))
                            leaf = int(clean_rt.getValue("Leaf", row))
                            mean = clean_rt.getValue("Mean", row)
                            f.write(image_name + "," + str(spot) + "," + str(leaf) + "," + str(mean) + "\n")
                    IJ.log("Results appended to: " + csv_path)
                else:
                    with open(csv_path, 'w') as f:
                        f.write("Image,Spot,Leaf,Mean\n")
                        for row in range(clean_rt.getCounter()):
                            spot = int(clean_rt.getValue("Spot", row))
                            leaf = int(clean_rt.getValue("Leaf", row))
                            mean = clean_rt.getValue("Mean", row)
                            f.write(image_name + "," + str(spot) + "," + str(leaf) + "," + str(mean) + "\n")
                    IJ.log("Results saved to: " + csv_path)