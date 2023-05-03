"""
Copyright (C) 2020 Abraham George Smith
Copyright (C) 2022 Abraham George Smith

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

#pylint: disable=I1101,C0111,W0201,R0903,E0611, R0902, R0914
import os
import numpy as np
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from progress_widget import BaseProgressWidget
from skimage.io import imread, imsave
from skimage import img_as_ubyte
from scipy.ndimage import binary_erosion, binary_dilation

class ConvertThread(QtCore.QThread):
    progress_change = QtCore.pyqtSignal(int, int)
    done = QtCore.pyqtSignal()

    def __init__(self, conversion_function, mask_dir, out_dir):
        super().__init__()
        self.mask_dir = mask_dir
        self.out_dir = out_dir
        self.conversion_function = conversion_function

    def run(self):
        mask_fnames = os.listdir(str(self.mask_dir))
        mask_fnames = [f for f in mask_fnames if os.path.splitext(f)[1] == '.png']
        for i, f in enumerate(mask_fnames):
            self.progress_change.emit(i+1, len(mask_fnames))
            if os.path.isfile(os.path.join(self.mask_dir, os.path.splitext(f)[0] + '.png')):
                # Load OnePainter mask and connvert.
                mask = imread(os.path.join(self.mask_dir, f))
                converted_mask = self.conversion_function(mask)
                imsave(os.path.join(self.out_dir, f),
                       converted_mask, check_contrast=False)
        self.done.emit()


def convert_mask_to_rve(bw):
    # Load mask and invert (white is foreground).
    rve_mask = (bw[:, :, 2] == 0)
    return img_as_ubyte(rve_mask)

def convert_mask_to_seg(bw):
    # Load OnePainter blue channel and invert (white is background).
    seg = np.zeros((bw.shape[0], bw.shape[1], 4))
    seg[bw > 0] = [0.0, 1.0, 1.0, 0.7] 
    return img_as_ubyte(seg)

def convert_mask_to_annot(msk, px=2, pxb=2):
    """
    Converts black/white masks to green/red annotations, respectively, with 
    optional shrinkage of annotations (default is by 2 pixels on each side)
    Input:
        msk : input mask
        px  : number of pixels to shrink foreground (red) mask by
        pxb : number of pixels to pull back background (green) mask by
    Output:
        foreground and background in red and green channels, respectively
    """
    ero = binary_erosion(msk, iterations=px)
    dil = binary_dilation(msk, iterations=pxb)
    annot = np.zeros((msk.shape[0], msk.shape[1], 4))
    annot[ero > 0]  = [1.0, 0, 0, 0.7] 
    annot[dil == 0] = [0, 1.0, 0, 0.7] 
    return img_as_ubyte(annot)

class ConvertProgressWidget(BaseProgressWidget):

    def __init__(self):
        super().__init__('Converting Masks')

    def run(self, convert_function, mask_dir, out_dir):
        self.mask_dir = mask_dir
        self.out_dir = out_dir
        self.thread = ConvertThread(convert_function, mask_dir, out_dir)
        mask_fnames = os.listdir(str(self.mask_dir))
        mask_fnames = [f for f in mask_fnames if os.path.splitext(f)[1] == '.png']
        self.progress_bar.setMaximum(len(mask_fnames))
        self.thread.progress_change.connect(self.onCountChanged)
        self.thread.done.connect(self.done)
        self.thread.start()

    def done(self):
        QtWidgets.QMessageBox.about(self, 'Masks Converted',
                                    f'Converting masks from {self.mask_dir} '
                                    f'to {self.out_dir} '
                                    'is complete.')
        self.close()


class ConvertMaskWidget(QtWidgets.QWidget):
    submit = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.mask_dir = None
        self.out_dir = None
        self.initUI()

    def initUI(self):
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.setWindowTitle("Convert masks")

        # Add specify mask directory button
        mask_dir_label = QtWidgets.QLabel()
        mask_dir_label.setText("Mask directory: Not yet specified")
        layout.addWidget(mask_dir_label)
        self.mask_dir_label = mask_dir_label

        specify_mask_btn = QtWidgets.QPushButton('Specify mask directory')
        specify_mask_btn.clicked.connect(self.select_mask_dir)
        layout.addWidget(specify_mask_btn)

        # Add specify output directory button
        out_dir_label = QtWidgets.QLabel()
        out_dir_label.setText("Output directory: Not yet specified")
        layout.addWidget(out_dir_label)
        self.out_dir_label = out_dir_label

        specify_out_dir_btn = QtWidgets.QPushButton('Specify output directory')
        specify_out_dir_btn.clicked.connect(self.select_out_dir)
        layout.addWidget(specify_out_dir_btn)

        convert_label = QtWidgets.QLabel()
        convert_label.setText(f"Selected Output: Annotations (.png)")
        layout.addWidget(convert_label)
        self.convert_label = convert_label
        self.convert_dropdown = QtWidgets.QComboBox()
        self.convert_dropdown.addItems(['Annotations (.png)', 'Segmentations (.png)',
                                       'RhizoVision Explorer format (.png)'])
        self.convert_dropdown.currentIndexChanged.connect(self.format_selection_change)
        layout.addWidget(self.convert_dropdown)

        info_label = QtWidgets.QLabel()
        info_label.setText("Mask directory and output directory"
                           " must be specified.")
        layout.addWidget(info_label)
        self.info_label = info_label

        submit_btn = QtWidgets.QPushButton('Convert Masks')
        submit_btn.clicked.connect(self.convert_masks)
        layout.addWidget(submit_btn)
        submit_btn.setEnabled(False)
        self.submit_btn = submit_btn

    def format_selection_change(self, _):
        self.convert_label.setText("Selected Output Format: " + self.convert_dropdown.currentText())

    def convert_masks(self):
        self.progress_widget = ConvertProgressWidget()
        format_str = self.convert_dropdown.currentText()
        if format_str == 'RhizoVision Explorer format (.png)':
            self.convert_function = convert_mask_to_rve
        elif format_str == 'Segmentations (.png)':
            self.convert_function = convert_mask_to_seg
        else:
            self.convert_function = convert_mask_to_annot
        self.progress_widget.run(self.convert_function, self.mask_dir, self.out_dir)
        self.progress_widget.show()
        self.close()

    def validate(self):
        if not self.mask_dir:
            self.info_label.setText("Mask directory must be "
                                    "specified to convert files.")
            self.submit_btn.setEnabled(False)
            return

        if not self.out_dir:
            self.info_label.setText("Output directory must be "
                                    "specified to convert files.")
            self.submit_btn.setEnabled(False)
            return

        self.info_label.setText("")
        self.submit_btn.setEnabled(True)

    def select_mask_dir(self):
        self.input_dialog = QtWidgets.QFileDialog(self)
        self.input_dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        def input_selected():
            self.mask_dir = self.input_dialog.selectedFiles()[0]
            self.mask_dir_label.setText('Mask directory: ' + self.mask_dir)
            self.validate()
        self.input_dialog.fileSelected.connect(input_selected)
        self.input_dialog.open()

    def select_out_dir(self):
        self.input_dialog = QtWidgets.QFileDialog(self)
        self.input_dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        def input_selected():
            self.out_dir = self.input_dialog.selectedFiles()[0]
            self.out_dir_label.setText('Output directory: ' + self.out_dir)
            self.validate()
        self.input_dialog.fileSelected.connect(input_selected)
        self.input_dialog.open()
