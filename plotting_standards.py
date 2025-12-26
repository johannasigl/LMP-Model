"""
Plotting Standards for Neon
"""

import matplotlib.pyplot as plt
import numpy as np
from cycler import cycler
from matplotlib.patches import Circle
import warnings
from labellines import labelLines

# ... (plot_sizes and setup_plotting_standards remain the same) ...
# Plot sizes (width x height in cm)
plot_sizes = {
    'large': (30.5, 12),
    'mid': (19, 12),
    'small': (13.3, 12)
}

def setup_plotting_standards():
    """
    Configure matplotlib with project-wide plotting standards.
    Call this function at the beginning of your analysis scripts.
    """
    plt.rcParams.update({'font.sans-serif' : 'Calibri',
                    'font.weight' : 'light',
                    'figure.dpi' : 150,
                    'savefig.dpi' : 300,
                    'axes.labelweight' : 'light',
                    'font.size': 10, 
                    'font.style': 'normal', 
                    'axes.xmargin': 0.01,
                    'axes.titlecolor': '#4B8246',
                    'axes.titlelocation': 'left',
                    'axes.titlepad': 6.0,
                    'axes.titlesize': 16,
                    'axes.titleweight': 'light',
                    'figure.titlesize': 16,
                    'figure.titleweight': 'light',
                    'grid.color': 'lightgray',
                    'axes.grid': True,
                    'axes.grid.axis': 'y',
                    'axes.axisbelow': True,
                    'yaxis.labellocation': 'top',
                    'axes.spines.right': False,
                    'axes.spines.top': False,
                    'axes.spines.left': False,
                    'ytick.left': False,
                    'axes.titlepad' : 20,
                    'axes.prop_cycle' : cycler(color=['#BAD1AC', '#4B8246', '#FFD966', '#7F7F7F', '#D9D9D9', '#4061A4', '#D26A5E']), # light green, dark green, yellow, gray, blue, smokey red
                    'patch.edgecolor': '#595959',
                    'patch.linewidth': 0.8,
                    'axes.edgecolor': '#969696',  # <-- x-axis color
                    'xtick.color': '#969696',
                    'xtick.labelcolor': '#595959',  # <-- xtick label color
                    'ytick.labelcolor': '#595959',  # <-- ytick label color
                    'axes.labelcolor': '#595959',   # <-- x- and y-label color
                    'legend.labelcolor': '#595959', # <-- legend text color
                    'lines.markeredgecolor': '#595959',
                    'lines.markeredgewidth': 0.5,  
                    'text.color': '#595959',
                    })

# ... (draw_logo, add_unit_to_top_ytick, add_logo_to_figure, place_title remain the same) ...
def draw_logo(ax, fig, logo_linewidth):
    ''' 
    Draws an artificial Neon logo on the given matplotlib Axes.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes on which to draw the logo.
    fig : matplotlib.figure.Figure
        The figure object, used to determine scaling based on figure size.
    logo_linewidth : float
        Linewidth of the logo in points (pt). This is absolute and independent of logo size.

    Notes
    -----
    - The logo consists of a stylized Y-shape, a ring, and three vertical bars.
    - The logo is scaled proportionally to the axes size, but linewidth is constant.
    - The axes are modified to fit the logo and are turned off for display.
    '''
    # Reference logo size (in arbitrary units)
    ref_width, ref_height = 350, 120

    # --- Draw the artificial logo ---
    line_color = 'black'

    # Y-shape
    center_x, center_y = 62, 60
    branch_length = 56
    angle = np.deg2rad(60)
    ax.plot([center_x, center_x - branch_length], [center_y, center_y], color=line_color, linewidth=logo_linewidth, solid_capstyle='butt')
    ax.plot([center_x, center_x + branch_length * np.cos(angle)], [center_y, center_y + branch_length * np.sin(angle)], color=line_color, linewidth=logo_linewidth, solid_capstyle='butt')
    ax.plot([center_x, center_x + branch_length * np.cos(-angle)], [center_y, center_y + branch_length * np.sin(-angle)], color=line_color, linewidth=logo_linewidth, solid_capstyle='butt')

    # Ring
    ring_center = (177, 60)
    ring_radius = 43
    ring = Circle(ring_center, ring_radius, edgecolor=line_color, facecolor='none', linewidth=logo_linewidth)
    ax.add_patch(ring)

    # Vertical bars
    bar_base_x = 266
    bar_base_y = 11
    bar_spacing = 25
    bar_heights = [38, 63, 98]
    for i, height in enumerate(bar_heights):
        x_pos = bar_base_x + i * bar_spacing
        ax.plot([x_pos, x_pos], [bar_base_y, bar_base_y + height], color=line_color, linewidth=logo_linewidth, solid_capstyle='butt')

    # Set limits so the logo fits
    ax.set_xlim(0, ref_width)
    ax.set_ylim(0, ref_height)
    ax.axis('off')

def add_unit_to_top_ytick(fig, ax, unit):
    """
    Annotate the unit next to the topmost y-tick for one or more axes.
    Parameters
    ----------
    ax : matplotlib.axes.Axes or array of Axes
        The axes to annotate. If an array, annotates each one.
    unit : str or list of str
        The unit string(s) to display. If a list, its length must match the number of axes.
    """
    axes = np.atleast_1d(ax).flatten()
    units = [unit] * len(axes) if isinstance(unit, str) else unit

    if len(units) != len(axes):
        raise ValueError(f"The number of units ({len(units)}) must match the number of subplots ({len(axes)}).")

    for i, current_ax in enumerate(axes):
        current_unit = units[i]
        if not current_unit:  # Skip if unit is None or empty
            continue

        yticks = current_ax.get_yticks()
        if len(yticks) == 0:
            continue

        y_min, y_max = current_ax.get_ylim()
        axis_height_cm = current_ax.get_window_extent().height / fig.dpi * 2.54
        data_per_cm = (y_max - y_min) / axis_height_cm if axis_height_cm > 0 else 0

        # Find the topmost visible ytick (not too close to the edge)
        # Define a tolerance for 'too close' (e.g., within 1% of axis range)
        tol = 0.001 * (y_max - y_min)
        # Start from the last ytick and move down if needed
        top_y = yticks[-1]
        if (top_y - y_max) > tol:
            # If top_y is too close to y_max, use the next lower ytick if available
            if len(yticks) > 1:
                top_y = yticks[-2]
        # Shift top_y down by 0.03 cm in data units
        top_y = top_y - 0.03 * data_per_cm

        current_ax.annotate(
            current_unit,
            xy=(0, top_y),
            xycoords=('axes fraction', 'data'),
            va='center',
            ha='left',
            fontsize=current_ax.yaxis.get_label().get_size(),
            color=current_ax.yaxis.get_label().get_color() if hasattr(current_ax.yaxis.get_label(), 'get_color') else 'black',
            annotation_clip=False,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none")
        )

def add_logo_to_figure(fig, ax, logo='SE', logo_size_cm=(1.6*0.6, 0.544*0.6), logo_margin_cm=0.3*0.6, logo_linewidth=0.6):
    """
    Adds an artificial logo to the figure, positioned relative to an axis or group of axes.
    If `ax` is an array, the logo is placed relative to the bottom-right axis ('SE', 'SW').
    Legacy logo size:  logo_size_cm=(1.6, 0.544)
    """
    # Convert logo size and margin from cm to inches
    logo_width_inch = logo_size_cm[0] / 2.54
    logo_height_inch = logo_size_cm[1] / 2.54
    logo_margin_inch = logo_margin_cm / 2.54

    # Determine the reference axis from a potential array of axes
    axes_array = np.atleast_1d(ax)
    if logo in ['SE', 'SW']:
        ref_ax = axes_array[-1] if axes_array.ndim == 1 else axes_array[-1, -1] # Bottom-rightmost axis
    else: # NE, NW
        ref_ax = axes_array[0] if axes_array.ndim == 1 else axes_array[0, -1] # Top-rightmost axis

    # Get axes bounding box in figure coordinates
    ax_bbox = ref_ax.get_position()
    fig_w, fig_h = fig.get_size_inches()

    # Calculate logo position in figure coordinates
    if logo == 'SE':
        x0 = ax_bbox.x1 * fig_w - logo_width_inch - logo_margin_inch
        y0 = ax_bbox.y0 * fig_h + logo_margin_inch
    elif logo == 'SW':
        x0 = ax_bbox.x0 * fig_w + logo_margin_inch
        y0 = ax_bbox.y0 * fig_h + logo_margin_inch
    # elif logo == 'NE':
    #     x0 = ax_bbox.x1 * fig_w - logo_width_inch - logo_margin_inch
    #     y0 = ax_bbox.y1 * fig_h - logo_height_inch - logo_margin_inch + 0.2
    # elif logo == 'NW':
    #     x0 = ax_bbox.x0 * fig_w + logo_margin_inch
    #     y0 = ax_bbox.y1 * fig_h - logo_height_inch - logo_margin_inch + 0.2
    else:
        raise ValueError("logo must be one of 'SE', 'SW'")

    # Convert logo position and size to figure-relative coordinates
    x_rel = x0 / fig_w
    y_rel = y0 / fig_h
    w_rel = logo_width_inch / fig_w
    h_rel = logo_height_inch / fig_h

    # Create an inset axes for the logo
    logo_ax = fig.add_axes([x_rel, y_rel, w_rel, h_rel])
    draw_logo(logo_ax, fig, logo_linewidth)  # logo_scale sets linewidth, stays constant

def place_title(fig, ax, text):
    """
    Adds a suptitle to the figure. The x position is aligned relative to the
    leftmost axis' y-tick labels and is adjusted if a ylabel is present.
    """
    # Use the top-left axis for positioning calculations
    ref_ax = np.atleast_1d(ax).flatten()[0]

    fig_width = fig.get_size_inches()[0] * 2.54
    # Calculate offset based on number of digits in max ytick of all axes
    axes_flat = np.atleast_1d(ax).flatten()
    all_yticklabels = []
    for axis in axes_flat:
        all_yticklabels.extend(axis.get_yticklabels())
    
    if all_yticklabels:
        # Filter out empty labels before getting the max length
        non_empty_labels = [lbl.get_text() for lbl in all_yticklabels if lbl.get_text()]
        if non_empty_labels:
            num_digits = max(len(s) for s in non_empty_labels)
        else:
            num_digits = 3 # Default if labels are present but empty
    else:
        num_digits = 3 # Default if no labels

    digit_offset = (num_digits - 3) * 0.01  # adjust this factor as needed for spacing
    x_pos = 0.0022 * fig_width + 0.0431 - digit_offset * 13.3/fig_width

    # Add an additional offset if a ylabel is present on any axis
    if any(axis.get_ylabel() for axis in axes_flat):
        # This value is empirical and may need adjustment for different fonts/sizes
        ylabel_offset = 0.035 * 13.3/fig_width
        x_pos -= ylabel_offset

    fig.suptitle(
        text,
        fontsize=plt.rcParams.get('figure.titlesize', 16),
        fontweight=plt.rcParams.get('figure.titleweight', 'light'),
        color=plt.rcParams.get('axes.titlecolor', '#4B8246'),
        fontname=plt.rcParams.get('font.sans-serif', ['Calibri'])[0],
        x=x_pos,
        ha='left',
    )

class NeonFigure:
    """
    A wrapper around a matplotlib Figure that simplifies the creation of
    plots conforming to Neon's plotting standards.

    This class acts as a context manager, allowing users to create and
    modify the plot as they normally would with matplotlib. The custom
    styling (logo, title, units) is applied automatically upon exiting
    the `with` block.
    """
    def __init__(self, size='small', logo=None, title_text=None, 
                 unit=None, inline_label=False, labellines_kwargs=None, **kwargs):
        """
        Initializes the figure and stores styling parameters for later.

        Parameters
        ----------
        size : str or tuple
            Figure size, e.g., 'small', 'mid', 'large' or (width_cm, height_cm).
        logo : str, optional
            Logo position, e.g., 'SE', 'SW'.
        title_text : str, optional
            The main title for the figure.
        unit : str or list of str, optional
            Unit(s) for the y-axis/axes.
        inline_label : bool, optional
            If True, automatically add labels next to the lines.
        labellines_kwargs : dict or list of dict, optional
            Keyword arguments to pass to `labelLines`. If a dict, it's applied
            to all axes. If a list of dicts, each dict is applied to the
            corresponding axis.
        **kwargs :
            Additional keyword arguments passed to `plt.subplots` 
            (e.g., `nrows`, `ncols`, `sharex`).
        """
        setup_plotting_standards()
        
        # Store styling options for later
        self.logo = logo
        self.title_text = title_text
        self.unit = unit
        self.inline_label = inline_label
        self.labellines_kwargs = labellines_kwargs if labellines_kwargs is not None else {}
        
        # Determine figure size in inches
        if isinstance(size, str):
            width_cm, height_cm = plot_sizes[size]
        elif isinstance(size, (tuple, list)) and len(size) == 2:
            width_cm, height_cm = size
        else:
            raise ValueError("size must be one of 'small', 'mid', 'large' or a tuple/list of (width_cm, height_cm)")
        
        width_inch = width_cm / 2.54
        height_inch = height_cm / 2.54
        
        # Create the figure and axes
        self.fig, self.ax = plt.subplots(figsize=(width_inch, height_inch), **kwargs)

    def finalize(self):
        """
        Applies all stored Neon styling options to the figure.
        This method is called automatically when using a `with` statement.
        """
        # The figure must be drawn once for get_yticklabels and other elements to be ready
        self.fig.canvas.draw()

        if self.unit is not None:
            # Check if ylim is set on the axes, which is required for unit placement
            axes_flat = np.atleast_1d(self.ax).flatten()
            if all(ax.get_ylim() == (0.0, 1.0) for ax in axes_flat): # Default ylim
                 warnings.warn("Y-limits are not set. Unit placement may be incorrect. Please set ylim using ax.set_ylim().", UserWarning)
            add_unit_to_top_ytick(self.fig, self.ax, self.unit)

        if self.logo:
            add_logo_to_figure(self.fig, self.ax, self.logo)

        if self.title_text:
            place_title(self.fig, self.ax, self.title_text)
        
        if self.inline_label:
            axes_flat = np.atleast_1d(self.ax).flatten()
            
            # Determine if kwargs are provided per axis or globally
            is_list_of_kwargs = isinstance(self.labellines_kwargs, list)

            if is_list_of_kwargs and len(self.labellines_kwargs) != len(axes_flat):
                warnings.warn("The number of labellines_kwargs dictionaries does not match the number of axes. Applying globally.")
                is_list_of_kwargs = False

            for i, axis in enumerate(axes_flat):
                lines = axis.get_lines()
                if not lines:
                    continue

                # Default kwargs for labelLines
                fig_height = self.fig.get_size_inches()[1]
                y_min, y_max = axis.get_ylim()
                data_range = y_max - y_min
                offset = 0.8 * data_range / fig_height
                
                default_kwargs = {
                    'align': False,
                    'yoffsets': [offset] * len(lines)
                }
                
                # Get the specific kwargs for this axis
                if is_list_of_kwargs:
                    axis_kwargs = self.labellines_kwargs[i]
                else:
                    axis_kwargs = self.labellines_kwargs # It's a single dict

                # Merge user-provided kwargs, which will overwrite defaults
                # Overwrite default_kwargs only for keys present in axis_kwargs
                final_kwargs = default_kwargs.copy()
                for k in axis_kwargs:
                    final_kwargs[k] = axis_kwargs[k]
                
                labelLines(lines, **final_kwargs)
        
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finalize()


'''
Example Usage
-------------
The following section demonstrates how to use the Neon plotting standards module.
It provides two examples:
1. Using the `NeonFigure` context manager (recommended):
    - Automatically applies Neon styling, logo, title, and units when exiting the `with` block.
    - Supports multiple subplots and custom figure sizes.
2. Manual finalization:
    - Allows manual creation and modification of the figure.
    - Requires explicit call to `finalize()` to apply Neon styling before displaying the plot.
These examples illustrate typical workflows for generating publication-ready plots
with consistent Neon branding and formatting.
'''
if __name__ == "__main__":
    # --- Example 1: Using the context manager (recommended) ---
    print("Showing plot created with the context manager...")
    
    # Sample data
    x = np.linspace(0, 2 * np.pi, 20)
    y1 = np.sin(x)
    y2 = 100 * np.cos(x)

    with NeonFigure(size='mid', title_text='Context Manager Example', 
                    unit=['A', 'V'], logo='SE', nrows=2, sharex=True, inline_label=True) as nf:

        # nf.ax is the array of axes objects
        nf.ax[0].plot(x, y1, label = 'Current', marker='o')
        nf.ax[0].plot(x, -y1, label = 'Current 2', marker='o')
        nf.ax[0].plot(x, 0.5 * y1, label = 'Current 3', marker='o')
        nf.ax[0].set_ylim(-1.2, 1.2)

        nf.ax[1].plot(x, y2, label = 'Voltage', marker='o')
        nf.ax[1].set_ylim(-120, 120)
        nf.ax[1].set_xlabel('Angle [rad]')

        # Set custom label positions for each axis
        nf.labellines_kwargs = [
            {'xvals': (.5, 1, 5)},      # For the first axis (ax[0])
            {'xvals': (1,)}   # For the second axis (ax[1])
        ]

    plt.show()

    # --- Example 2: Manual finalization with custom label position ---
    print("\nShowing plot created with manual finalization and custom label position...")

    # Create the NeonFigure instance
    nf = NeonFigure(size='mid', title_text='Manual Finalization Example', unit='kg', logo='SW', 
                    inline_label=True, labellines_kwargs={'xvals': (np.pi,)})
    
    # nf.ax is the single axes object
    nf.ax.plot(x, -0.01 * np.sin(x), label = 'Mass', color = '#4B8246')
    nf.ax.set_ylim(-0.012, 0.012)
    # nf.ax.set_ylabel('Mass')
    nf.ax.set_xlabel('Angle [rad]')

    # Manually call finalize() before showing
    nf.finalize()
    plt.show()