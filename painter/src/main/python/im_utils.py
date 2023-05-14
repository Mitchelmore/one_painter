"""
Copyright (C) 2020 Abraham George Smith

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

# pylint: disable=C0111, W0511
import os
import warnings
import glob
import sys

import numpy as np
from PyQt5 import QtGui
from skimage import color
from skimage.io import imread, imsave
from skimage import img_as_ubyte
from skimage import img_as_float
from skimage.transform import resize
from skimage.color import rgb2gray
import qimage2ndarray
from PIL import Image, ImageOps
from scipy.ndimage import binary_dilation, binary_fill_holes

def is_image(fname):
    extensions = {".jpg", ".png", ".jpeg", '.tif', '.tiff'}
    return any(fname.lower().endswith(ext) for ext in extensions)


def all_image_paths_in_dir(dir_path):
    one_dir = os.path.abspath(dir_path)
    all_paths = glob.iglob(one_dir + '/**/*', recursive=True)
    image_paths = []
    for p in all_paths:
        name = os.path.basename(p)
        if name[0] != '.':
            ext = os.path.splitext(name)[1].lower()
            if ext in ['.png', '.jpg', '.jpeg', '.tif', '.tiff']:
                image_paths.append(p)
    return image_paths


def fpath_to_pixmap(fpath):
    """ Load image from fpath and convert to a PyQt5 pixmap object """
    np_im = load_image(fpath)
    # some (png) images were float64 and appeared very 
    # dark after conversion to pixmap.
    # convert to int8 to fix.
    np_im = img_as_ubyte(np_im) 
    q_image = qimage2ndarray.array2qimage(np_im)
    return QtGui.QPixmap.fromImage(q_image)

def load_image(photo_path):
    photo = Image.open(photo_path)

    # Convert to RGB before converting to NumPy due to bug in Pillow
    # https://github.com/Abe404/root_painter/issues/94
    photo = photo.convert("RGB") 

    photo = ImageOps.exif_transpose(photo)
    photo = np.array(photo)
    # sometimes photo is a list where first element is the photo
    if len(photo.shape) == 1:
        photo = photo[0]

    # JFIF files have an extra dimension at the start containing two elements
    # The first element is the image.
    if len(photo.shape) == 4 and photo.shape[0] == 2:
        photo = photo[0]

    # if 4 channels then convert to rgb
    # (presuming 4th channel is alpha channel)
    if len(photo.shape) > 2 and photo.shape[2] == 4:
        photo = color.rgba2rgb(photo)

    # if image is black and white then change it to rgb
    # TODO: train directly on B/W instead of doing this conversion.
    if len(photo.shape) == 2:
        photo = color.gray2rgb(photo)
    return photo


def save_masked_image(seg_dir, image_dir, output_dir, fname):
    """ useful for using segmentations to remove irrelvant information in an image
        as part of a pre-processing stage """
    seg = imread(os.path.join(seg_dir, fname))
    # use alpha channel if rgba
    if len(seg.shape) > 2:
        seg = seg[:, :, 2]
    im_path = os.path.join(image_dir, os.path.splitext(fname)[0]) + '.*'
    glob_results = glob.glob(im_path)
    if glob_results:
        im = imread(glob_results[0])
        im[seg==0] = 0 # make background black.
        imsave(os.path.join(output_dir, os.path.splitext(fname)[0] + '.jpg'), im, quality=95)

def save_corrected_segmentation(annot_fpath, seg_dir, output_dir):
    """assign the annotations (corrections) to the segmentations. This is useful
       to obtain more accurate (corrected) segmentations."""
    fname = os.path.basename(annot_fpath)
    seg = img_as_float(imread(os.path.join(seg_dir, fname)))
    annot = img_as_float(imread(annot_fpath))
    fg = annot[:, :, 0]
    bg = annot[:, :, 1]
    seg[bg > 0] = [0,0,0,0]
    seg[fg > 0] = [0, 1.0, 1.0, 0.7]
    imsave(os.path.join(output_dir, fname), seg)


def gen_composite(annot_dir, photo_dir, comp_dir, fname, ext='.jpg'):
    """ 
    Outputs the image together with an image-mask composite below it, where the mask 
    is transparent. Should make it possible to identify errors."""
    out_path = os.path.join(comp_dir, fname.replace('.png', ext))
    if not os.path.isfile(out_path):
        name_no_ext = os.path.splitext(fname)[0]
        # doesn't matter what the extension is
        glob_str = os.path.join(photo_dir, name_no_ext) + '.*'
        bg_fpath = list(glob.iglob(glob_str))[0]
        background = load_image(bg_fpath)
        annot = imread(os.path.join(annot_dir, os.path.splitext(fname)[0] + '.png'))
        if sys.platform == 'darwin':
            # resize uses np.linalg.inv and causes a segmentation fault
            # for very large images on osx
            # See https://github.com/bcdev/jpy/issues/139
            # Maybe switch to ATLAS to help (for BLAS)
            # until fixed, use simpler resize method.
            # take every second pixel
            background = background[::2, ::2]
            annot = annot[::2, ::2]
        else:
            background = resize(background,
                                (background.shape[0]//2,
                                 background.shape[1]//2, 3))
            annot = resize(annot, (annot.shape[0]//2, annot.shape[1]//2, annot.shape[2]))
        # if the annotation has 4 channels (that means alpha included)
        if len(annot.shape) and annot.shape[2] == 4:
            # then save alpha channel
            alpha_channel = annot[:, :, 3]
            # convert the annot to just the rgb
            annot = annot[:, :, :3]
            # and set to 0 if the alpha was 0
            annot[alpha_channel == 0] = [0, 0, 0]

        annot = rgb2gray(annot)
        #annot = img_as_ubyte(annot)
        background = img_as_ubyte(background)
        comp_right = np.copy(background)
        comp_right = img_as_float(comp_right)
        transp = comp_right * 0.3 + [0.7, 0, 0]
        comp_right[annot > 0] = transp[annot > 0]
        comp_right = img_as_ubyte(comp_right)
        # if width is more than 20% bigger than height then vstack
        #if background.shape[1] > background.shape[0] * 1.2:
        #    comp = np.vstack((background, comp_right))
        #else:
        #    comp = np.hstack((background, comp_right))
        # always stack vertically
        comp = np.vstack((background, comp_right))
        assert comp.dtype == np.uint8
        with warnings.catch_warnings():
            # avoid low constrast warning.
            warnings.simplefilter("ignore")
            imsave(out_path, comp, quality=95)

def fill_fg_bg(annot_pixmap):
    """
    Fills inside of foreground outline with foreground color and outwards of background 
    outline with background color. Requires at least one color on annotation.
    """
    fg, bg = get_fg_bg(annot_pixmap)
    if np.sum(fg) or np.sum(bg):
        # fill in foreground shape
        fg = binary_fill_holes(fg)
        # expand foreground shape to background border(s) to get inverted background
        inv = np.logical_not(bg) 
        bg_inv = binary_dilation(fg, iterations=-1, mask=inv)
        filled = np.zeros((fg.shape[0], fg.shape[1], 4))
        filled[fg > 0]  = [255, 0, 0, 180] 
        filled[bg_inv == 0] = [0, 255, 0, 180]
        filled_q = qimage2ndarray.array2qimage(filled)
        return QtGui.QPixmap.fromImage(filled_q)
    else:
        return annot_pixmap

def get_seg(seg_pixmap):
    seg_im = seg_pixmap.toImage()
    seg = np.array(qimage2ndarray.rgb_view(seg_im))[:, :, 2]
    return seg

def get_fg_bg(annot_pixmap):
    annot_im = annot_pixmap.toImage()
    annot_rgb = np.array(qimage2ndarray.rgb_view(annot_im))
    fg = annot_rgb[:, :, 0]
    bg = annot_rgb[:, :, 1]
    return fg, bg

def fill_corrective(annot_pixmap, seg_pixmap):
    """
    Fills inside of foreground outline with foreground color and, only for segmented components, 
    outwards of background outline with background color. Requires at least one color on annotation.
    """
    fg, bg = get_fg_bg(annot_pixmap)
    seg = get_seg(seg_pixmap)
    if np.sum(fg) or np.sum(bg):
        # fill in foreground shape
        fg = binary_fill_holes(fg)
        # expand foreground shape to background border(s) to get inverted background
        inv = np.logical_not(bg) 
        bg_inv = binary_dilation(fg, iterations=-1, mask=inv)
        filled = np.zeros((fg.shape[0], fg.shape[1], 4))
        filled[seg > 0]    = [0, 255, 0, 180] 
        filled[bg_inv > 0] = [0, 0, 0, 0] 
        filled[fg > 0]     = [255, 0, 0, 180]
        filled_q = qimage2ndarray.array2qimage(filled)
        return QtGui.QPixmap.fromImage(filled_q)
    else:
        return annot_pixmap
    
def seg_fill_fg(annot_pixmap, seg, x, y):
    """
    Selects a connected component in blue channel and flood-fills with foreground color,
    up to any background border, in annotation.
    """
    fg, bg = get_fg_bg(annot_pixmap)
    # get mask for seg, fg and inverted background, then flood-fill with foreground
    seg_new = np.zeros((seg.shape[0], seg.shape[1]), dtype=int)
    seg_new[seg > 0] = 1
    seg_new[bg > 0]  = 0
    seg_fg = np.zeros((seg.shape[0], seg.shape[1]), dtype=int)
    seg_fg[y, x] = 1
    seg_fg = binary_dilation(seg_fg, iterations=-1, mask=seg_new)
    filled = np.zeros((fg.shape[0], fg.shape[1], 4))
    filled[seg_fg > 0] = [255, 0, 0, 180] 
    filled[fg > 0]     = [255, 0, 0, 180] 
    filled[bg > 0]     = [0, 255, 0, 180]
    filled_q = qimage2ndarray.array2qimage(filled)
    return QtGui.QPixmap.fromImage(filled_q)

def unfill_cc(annot_pixmap, msk, x, y):
    """
    Selects and un-colors a connected component in annotation.
    """
    fg, bg = get_fg_bg(annot_pixmap)
    # get mask for colored component, then flood-fill with 0's
    msk_new = np.zeros((msk.shape[0], msk.shape[1]), dtype=int)
    msk_new[msk > 0] = 1
    cc = np.zeros((msk.shape[0], msk.shape[1]), dtype=int)
    cc[y, x] = 1
    cc = binary_dilation(cc, iterations=-1, mask=msk_new)
    filled = np.zeros((fg.shape[0], fg.shape[1], 4))
    filled[fg > 0] = [255, 0, 0, 180] 
    filled[bg > 0] = [0, 255, 0, 180]
    filled[cc > 0] = [0, 0, 0, 0]
    filled_q = qimage2ndarray.array2qimage(filled)
    return QtGui.QPixmap.fromImage(filled_q)

def corrected_seg(annot_fpath, seg_dir, fname):
    """assign the annotations (corrections) to the segmentations. This is useful
       to obtain more accurate (corrected) segmentations."""
    seg = img_as_float(imread(os.path.join(seg_dir, fname)))
    annot = img_as_float(imread(annot_fpath))
    fg = annot[:, :, 0]
    bg = annot[:, :, 1]
    seg[bg > 0] = [0,0,0,0]
    seg[fg > 0] = [0, 1.0, 1.0, 0.7]
    return seg