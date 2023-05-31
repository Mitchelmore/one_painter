## OnePainter

I made some customised changes to the original RootPainter code, which I call OnePainter. OnePainter is intended for interactive segmentation of single, solid regions, such as tumours, in 2D images. It is based on RootPainter, but uses automatic filling-in/out to make dense annotations, includes some extra functions, and the segmentation result includes an option to show only the largest predicted region. 

Changes with respect to RootPainter:

User paints a perimeter around the background and foreground (it doesn't matter if there are other marks, as long as they are in the same color as the delineating perimeter), and the software automatically flood-fills foreground to the outer red perimeter, and background to the inner-most green perimeter when the user saves and moves on to the next image. If only green is used, the whole annotation is saved as green (e.g. if no tumor is present). The user can optionally click on a 'Save' button to see the auto-fill before moving to the next image.

The user can optionally start a corrective-fill mode, which only labels false-positive segmentation as background, rather than flood-filling the background. Otherwise, it fills as above.

When the eraser-brush is active, the user can press the ALT-key and click on an annotation to unfill color in the whole selected component.

When the brush color is red and the segmentation is visible, the user can press the ALT-key and click on a segmentation to fill it with foreground color. If the user has drawn green on the segmentation, this function will only fill the selected segmentation up to the green border.

After training is complete, the 'Segment Folder' command has an option to return only the closed, filled-in largest component. The user can also choose to return the two largest components. The default is all segmented regions (the RootPainter default).

The 'Extract composites' option always returns vertically stacking of image and composite, and the segmentation in the composite is transparent.

The 'Extra menu' now includes 'Convert segmentations' and 'Convert classical B/W masks' options for pre- and post-processing, e.g.  classical B/W masks can be converted to segmentations or annotations for use in OnePainter. The 'Correct annotations' was also modified to include different output options.

The code is based on RootPainter (github.com/Abe404/root\_painter) up to April 1, 2023, and includes code changes from RootPainter that enable extraction of annotation times.
______________
## RootPainter

RootPainter is a GUI-based software tool for the rapid training of deep neural networks for use in biological image analysis. 
RootPainter uses a client-server architecture, allowing users with a typical laptop to utilise a GPU on a more computationally powerful server.  

A detailed description is available in the paper published in the New Phytologist  [RootPainter: Deep Learning Segmentation of Biological Images with Corrective Annotation](https://doi.org/10.1111/nph.18387)

![RootPainter Interface](https://user-images.githubusercontent.com/376295/224013411-cb44c7c2-5c72-4819-98a3-6c0ab8b9ea4d.png)

To see a list of work using (or citing) the RootPainter paper, please see the [google scholar page](https://scholar.google.com/scholar?cites=12740268016453642124)

A BioRxiv Pre-print (earlier version of the paper) is available at:
[https://www.biorxiv.org/content/10.1101/2020.04.16.044461v2](https://www.biorxiv.org/content/10.1101/2020.04.16.044461v2)


### Getting started quickly

 I suggest the [colab tutorial](https://colab.research.google.com/drive/104narYAvTBt-X4QEDrBSOZm_DRaAKHtA?usp=sharing).
 
 A  shorter [mini guide](https://github.com/Abe404/root_painter/blob/master/docs/mini_guide.md) is available including more concise instruction, that could be used as reference. I suggest the paper, videos and then colab tutorial to get an idea of how the software interface could be used and then this mini guide for reference to help remember each of the key steps to get from raw data to final measurements. 
 
 
 

 
### Videos
A video demonstrating how to train and use a model is available to [download](https://nph.onlinelibrary.wiley.com/action/downloadSupplement?doi=10.1111%2Fnph.18387&file=nph18387-sup-0002-VideoS1.mp4)

There is a [youtube video](https://www.youtube.com/watch?v=73u73tBvRO4) of a workshop explaining the background behind the software and covering using the colab notebook to train and use a root segmentation model.


### Client Downloads

See [releases](https://github.com/Abe404/root_painter/releases) 

If you are not confident installing and running python applications on the command line then to get started quickly I suggest the [colab tutorial](https://colab.research.google.com/drive/104narYAvTBt-X4QEDrBSOZm_DRaAKHtA?usp=sharing).

#### Server setup 

The following instructions are for a local server. If you do not have a suitable NVIDIA GPU with at least 8GB of GPU memory then my current recommendation is to run via Google colab. A publicly available notebook is available at [Google Drive with Google Colab](https://colab.research.google.com/drive/104narYAvTBt-X4QEDrBSOZm_DRaAKHtA?usp=sharing).

Other options to run the server component of RootPainter on a remote machine include the [the sshfs server setup tutorial](https://github.com/Abe404/root_painter/blob/master/docs/server_setup_sshfs.md). You can also use Dropbox instead of sshfs.


For the next steps I assume you have a suitable GPU and CUDA installed.

1. To install the RootPainter trainer:

```
pip install root-painter-trainer
```

2. To run the trainer.  This will first create the sync directory.

```
start-trainer
```

You will be prompted to input a location for the sync directory. This is the folder where files are shared between the client and server. I will use ~/root_painter_sync.
RootPainter will then create some folders inside ~/root_painter_sync.
The server should print the automatically selected batch size, which should be greater than 0. It will then start watching for instructions from the client.

You should now be able to see the folders created by RootPainter (datasets, instructions and projects) inside ~/Desktop/root_painter_sync on your local machine 
See [lung tutorial](docs/cxr_lung_tutorial.md) for an example of how to use RootPainter to train a model. I now actually suggest following the [colab tutorial](https://colab.research.google.com/drive/104narYAvTBt-X4QEDrBSOZm_DRaAKHtA?usp=sharing) instructions but using your local setup instead of the colab server, as these are easier to follow than the lung tutorial.


 ### Questions and Problems
 
The [FAQ](https://github.com/Abe404/root_painter/blob/master/docs/FAQ.md) may  be worth checking before reaching out with any questions you have. If you do have a question you can either email me or post in the [discussions](https://github.com/Abe404/root_painter/discussions). If you have an issue/ have identified a problem with the software then you can [post an issue](https://github.com/Abe404/root_painter/issues).
