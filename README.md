# 🤖 SpotBot

**Interactive Leaf-by-Leaf Fluorescence Analysis Tool for ImageJ/Fiji** 🌿

[![Version](https://img.shields.io/badge/Version-2.5.0-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![ImageJ](https://img.shields.io/badge/ImageJ-Fiji%201.54+-blue.svg)](https://fiji.sc/)
[![Language](https://img.shields.io/badge/Language-Jython-yellow.svg)](https://www.jython.org/)

---

SpotBot automates the detection and quantification of fluorescent spots on plant leaves. It replaces tedious manual measurement of dozens of small fluorescent regions with an interactive, semi-automated workflow that assigns spots to individual leaves and exports organized results. 🎯

## ✨ Features

- 🎛️ **Interactive threshold adjustment** &mdash; real-time preview with yellow outlines as you tweak sliders
- 🍃 **Automatic leaf segmentation** &mdash; watershed-based separation of individual leaves
- 📍 **Automatic spot-to-leaf assignment** &mdash; spots assigned to leaves based on spatial overlap
- ✏️ **Manual ROI editing** &mdash; resize, move, delete, or add spots and negative controls
- 🖱️ **Interactive spot ordering** &mdash; click spots in your desired measurement sequence per leaf (red → blue)
- 📊 **Mean intensity measurement** per spot, organized by leaf and click order
- 💾 **Auto-save** &mdash; results automatically exported as CSV

## 📋 Requirements

- [Fiji](https://fiji.sc/) (ImageJ 1.54 or later)
- Jython interpreter (included with Fiji by default)

## 🚀 Installation

1. Download [`SpotBot.py`](SpotBot.py) from this repository
2. Place it anywhere on your computer (e.g. your Fiji `plugins/` folder, or any convenient location)
3. That's it &mdash; no additional dependencies required! 🎉

## 🔧 Usage

1. **Open** your fluorescence image in Fiji
2. **Run** SpotBot via `Plugins > Macros > Run...` and select `SpotBot.py`
3. **Adjust spot thresholds** &mdash; use the interactive sliders for intensity and minimum size. Yellow outlines show detected spots in real time
4. **Adjust leaf threshold** &mdash; fine-tune leaf detection with the threshold slider
5. **Edit ROIs** *(optional)* &mdash; resize, move, delete, or add spots
6. **Order spots** &mdash; for each leaf, click spots in your desired measurement order. Clicked spots turn from 🔴 red to 🔵 blue
7. **View results** &mdash; the results table displays measurements organized by leaf

### 🗺️ Workflow

```
📂 Open Image
     │
     ▼
🎛️  Spot Threshold  (interactive slider + live preview)
     │
     ▼
🍃  Leaf Detection  (interactive threshold)
     │
     ▼
📍  Spot-to-Leaf Assignment  (automatic)
     │
     ▼
✏️  Edit ROIs?  (optional: resize / move / delete / add)
     │
     ▼
🖱️  Order Spots  (click per leaf in measurement order)
     │
     ▼
📊  Results Table  (measurements grouped by leaf)
```

## 📤 Output

SpotBot generates a clean results table with three columns per spot:

| Column | Description |
|---|---|
| **Spot** | Spot number (click order within each leaf) |
| **Leaf** | Assigned leaf number |
| **Mean** | Mean fluorescence intensity |

Results are automatically saved as a CSV file in the same directory as the input image. 💾

## 👤 Author

**Nick Eilmann**
- 📧 Email: nme122@ic.ac.uk
- 🐙 GitHub: [@ne1899](https://github.com/ne1899)

## 📝 Citation

If you use SpotBot in your research, please cite:

> Eilmann N. (2026). SpotBot: Interactive Leaf-by-Leaf Fluorescence Analysis Tool for ImageJ/Fiji. https://github.com/ne1899/SpotBot

## 📄 License

This project is licensed under the MIT License &mdash; see the [LICENSE](LICENSE) file for details.
