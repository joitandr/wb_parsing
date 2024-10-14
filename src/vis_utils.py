import numpy as np
from PIL import Image
from PIL.Image import Image as ImageType
from numpy import typing as npt
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes._axes import Axes


def plot_image_with_mask(
    image: ImageType,
    mask: npt.NDArray[bool],
    fig: t.Optional[Figure]=None,
    ax: t.Optional[Axes]=None,
    figsize: t.Optional[t.Tuple[int]]=None,
) -> (Figure, Axes):
  
  if fig is None or ax is None:
    fig, ax = plt.subplots(figsize=(7, 7) if figsize is None else figsize)

  # Ensure the mask has the same dimensions as the image
  mask_resized = Image.fromarray((mask * 255).astype(np.uint8))  # Convert mask to an image
  mask_resized = mask_resized.resize(image.size, Image.NEAREST)  # Resize to match the image size

  # Convert mask to RGBA if it's binary
  mask_rgba = mask_resized.convert("RGBA")
  mask_rgba = np.array(mask_rgba)

  # Create a colored mask (e.g., red) and apply it to the mask's alpha channel
  colored_mask = np.zeros_like(mask_rgba)
  colored_mask[..., 0] = 200  # Red channel
  # colored_mask[..., 3] = mask_rgba[..., 0]  # Alpha channel from the original mask

  # Set the transparency level (0.0 - fully transparent, 1.0 - fully opaque)
  transparency_level = 1.0  # Adjust this value for desired transparency
  colored_mask[..., 3] = (mask_rgba[..., 0] / 255) * 255 * transparency_level  # Alpha channel from the original mask

  # Convert image to RGBA
  image_rgba = image.convert("RGBA")
  image_rgba = np.array(image_rgba)

  # Overlay the colored mask
  combined_image = Image.fromarray(np.where(colored_mask[..., 3:] > 0, colored_mask, image_rgba))

  # Display the result
  ax.imshow(combined_image)
  ax.axis('off')  # Hide axes
  fig.show()
  return fig, ax 

