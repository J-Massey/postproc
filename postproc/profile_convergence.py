# -*- coding: utf-8 -*-"""@author: J. Massey@description: Module to hold all the various convergence tests for a series of simulations. This    will provide the tools to show that a simulation has converged.@contact: jmom1n15@soton.ac.uk"""# Importsimport numpy as npimport postprocfrom postproc import cylinder_forces as cffrom postproc import iofrom postproc import plotterimport matplotlib.pyplot as pltimport osimport torchdevice = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")def plot_poincare(x, y, file, x_label, y_label, title=None, alpha=0.15, color='red', colours=None, label=None):    ax = plt.gca()    fig = plt.gcf()    ax.set_title(title)    # Loop so that lines get darker when they overlap    for i in range(len(x) - 1):        ax.plot(x[i:i + 2], y[i:i + 2], alpha=alpha, color=color, solid_capstyle="butt")    ax.tick_params(bottom="on", top="on", right="on", which='both', direction='in', length=2)    # Edit frame, labels and legend    ax.set_xlabel(x_label)    ax.set_ylabel(y_label)    # Make legend manually so that we don't try and label each line segment    from matplotlib.lines import Line2D    legend_elements = []    for idx, loop in enumerate(label):        legend_elements.append(Line2D([0], [0], color=colours[idx], lw=4, label=loop))    ax.legend(handles=legend_elements, loc='lower right')    # Show plot and save figure    plt.savefig(file, transparent=False, bbox_inches='tight')    returnclass ProfileDataset:    """    This class takes an input of a convergence test directory and returns the resolution,    angle around the circle, a list of the velocities at discrete spacings. And the l1    distance between consecutive profiles.    For this class to work your simulation folders must be structured as:    |+-- data_root    |   +-- profiles    Where the profiles subdirectory will have been printed using the all_profiles function in    utils.f90. These should be printed as consecutive x and y components e.g.:    ```    call all_profile(ave_v0%e(1), 256, 4.*D, angle)    call all_profile(ave_v0%e(2), 256, 4.*D, angle)    ```    """    def __init__(self, data_root):        self.conditions = []        self.angles = []        self.profiles_x = []        self.profiles_y = []        self.profiles_r = []        self.profiles_azi = []        os.listdir(data_root) == 'profiles'        profiles_folder = os.path.join(data_root, 'profiles')        self.step_angle = np.pi / len(os.listdir(profiles_folder))        for angle in os.listdir(profiles_folder):            angle_file = os.path.join(profiles_folder, angle)            profile = np.genfromtxt(angle_file)            theta = (float(angle) - 1) * self.step_angle            transform = [np.cos(theta), np.sin(theta)]            self.profiles_x.append(profile[::2])            self.profiles_y.append(profile[1::2])            self.profiles_r.append(profile[::2] * transform[0])            self.profiles_azi.append(profile[1::2] * transform[1])            self.angles.append(theta)    def upstream(self, name, cutoff=np.pi / 2):        """        Function to extract the l1 distance between consecutive upstream profiles to ensure they have converged        in time and space. In future this could be much more clever and have a cut off when the flow has        separated.        """        tmp = []        for idx, ang in enumerate(self.angles):            if ang <= cutoff:                tmp.append(name[idx])        return tmp    def bl_poincare_limit(self, single_point=True, position=0.24, length_scale=32, print_len=4, print_res=256):        """        Process the profile data so the x and y components of profiles either as single point in        that profile or as a sum of the whole BL        all the parts to encompass the whole profile.        :param single_point: Whether the BL should by analysed as a single point or an integral over the                            the whole profile.        :param position: The percentage of the diameter the BL profile is evaluated at        :param length_scale: The length scale of the simulation        :param print_len: How many length scales away from the body centre the profiles print.        :param print_res: How many points are printed when the print function is called        :return: Poincaré limit cycle at different angles around the profile.        """        import math        # Length of points depending on the resolution chosen for the print function        len_print = print_res / print_len        # The ratio between the print resolution and the actual grid spacing        len_res = print_res / (print_len * length_scale)        # About where the smoothing region ends in terms of the print resolution        eps = 2 * len_res        if single_point:            # Check if the evaluation point is at least 3 grid cells from the body boundary            eval_point = position * len_print            if eval_point < eps * 1.5:                raise ValueError("The evaluation point sits too close to the smoothing region,\                                    try adjusting the 'position' or increase your resolution")            else:                radial = []                azimuthal = []                for idx_angle, (loop_angle_x, loop_angle_y) in enumerate(zip(self.profiles_x, self.profiles_y)):                    tmp_r = np.array([])                    tmp_a = np.array([])                    for loop_time_x, loop_time_y in zip(loop_angle_x, loop_angle_y):                        # Index to the profile list rounded away from boundary to avoid smoothing region                        idx = math.ceil((0.5 + position) * len_print)                        theta = self.angles[idx_angle]                        transform = [np.cos(theta), np.sin(theta)]                        tmp_r = np.append(tmp_r, loop_time_x[idx]*transform[0])                        tmp_a = np.append(tmp_a, loop_time_y[idx]*transform[1])                    radial.append(tmp_r)                    azimuthal.append(tmp_a)            return radial, azimuthal        else:            radial = []            azimuthal = []            for idx_angle, (loop_angle_x, loop_angle_y) in enumerate(zip(self.profiles_x, self.profiles_y)):                tmp_r = np.array([])                tmp_a = np.array([])                for loop_time_x, loop_time_y in zip(loop_angle_x, loop_angle_y):                    theta = self.angles[idx_angle]                    transform = [np.cos(theta), np.sin(theta)]                    tmp_r = np.append(tmp_r, np.sum(loop_time_x)*transform[0])                    tmp_a = np.append(tmp_a, np.sum(loop_time_y)*transform[1])                radial.append(tmp_r)                azimuthal.append(tmp_a)            return radial, azimuthal