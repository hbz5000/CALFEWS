import numpy as np
import pandas as pd
import collections as cl
import toyplot as tp
import calendar
import scipy.stats as stats
from .reservoir import Reservoir
import math
import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import gridspec
from matplotlib.lines import Line2D
from .util import *
import seaborn as sns

class Inputter():

    def __init__(self, input_data_file, expected_release_datafile, model_mode):
        self.df = pd.read_csv(input_data_file, index_col=0, parse_dates=True)
        self.df_short = pd.read_csv(expected_release_datafile, index_col=0, parse_dates=True)
        self.T = len(self.df)
        self.index = self.df.index
        self.day_year = self.index.dayofyear
        self.day_month = self.index.day
        self.month = self.index.month
        self.year = self.index.year
        self.starting_year = self.year[0]
        self.ending_year = self.year[-1]
        self.number_years = self.ending_year - self.starting_year
        self.dowy = water_day(self.day_year, self.year)
        self.water_year = water_year(self.month, self.year, self.starting_year)

        self.leap = leap(np.arange(min(self.year), max(self.year) + 2))
        year_list = np.arange(min(self.year), max(self.year) + 2)
        self.days_in_month = days_in_month(year_list, self.leap)
        self.dowy_eom = dowy_eom(year_list, self.leap)
        self.non_leap_year = first_non_leap_year(self.dowy_eom)
        self.leap_year = first_leap_year(self.dowy_eom)

        self.shasta = Reservoir(self.df, self.df_short, 'SHA', model_mode)
        self.folsom = Reservoir(self.df, self.df_short, 'FOL', model_mode)
        self.oroville = Reservoir(self.df, self.df_short, 'ORO', model_mode)
        self.yuba = Reservoir(self.df, self.df_short, 'YRS', model_mode)

        self.newhogan = Reservoir(self.df, self.df_short, 'NHG', model_mode)
        self.pardee = Reservoir(self.df, self.df_short, 'PAR', model_mode)
        self.consumnes = Reservoir(self.df, self.df_short, 'MHB', model_mode)

        # 3 San Joaquin River Reservoirs (to meet Vernalis flow targets)
        self.newmelones = Reservoir(self.df, self.df_short, 'NML', model_mode)
        self.donpedro = Reservoir(self.df, self.df_short, 'DNP', model_mode)
        self.exchequer = Reservoir(self.df, self.df_short, 'EXC', model_mode)

        # Millerton Reservoir (flows used to calculate San Joaquin River index, not in northern simulation)
        self.millerton = Reservoir(self.df, self.df_short, 'MIL', model_mode)

        self.pineflat = Reservoir(self.df, self.df_short, 'PFT', model_mode)
        self.kaweah = Reservoir(self.df, self.df_short, 'KWH', model_mode)
        self.success = Reservoir(self.df, self.df_short, 'SUC', model_mode)
        self.isabella = Reservoir(self.df, self.df_short, 'ISB', model_mode)

        self.reservoir_list = [self.shasta, self.oroville, self.folsom, self.yuba, self.newmelones, self.donpedro,
                               self.exchequer, self.millerton, self.pineflat, self.kaweah, self.success, self.isabella,
                               self.newhogan, self.pardee, self.consumnes]
        self.data_type_list = ['fnf', 'inf', 'otf', 'gains', 'evap', 'precip', 'fci']
        self.monthlist = ["Jan", "Feb", "Mar", "Apr", "May", "June", "July", "Aug", "Sept", "Oct", "Nov", "Dec"]

        self.delta_list = ['SAC', 'SJ', 'EAST', 'depletions', 'CCC', 'BRK']

        sns.set()

    def run_routine(self, file_folder, file_name, timestep_length, start_month, number_years, first_leap,
                    start_timestep, end_timestep, start_year):
        print('Load New Full-Natural Flows from ' + file_name)
        self.read_new_fnf_data(file_folder + file_name, timestep_length, start_month, first_leap, number_years)
        self.whiten_by_historical_moments(number_years, 'XXX')
        self.whiten_by_historical_moments_delta(number_years, 'XXX')
        self.make_fnf_prediction(number_years, 'XXX')
        self.make_fnf_prediction_delta(number_years, 'XXX')
        self.find_residuals(start_month, number_years, 'XXX')
        self.find_residuals_delta(start_month, number_years, 'XXX')
        self.add_error(number_years, 'XXX')
        self.add_error_delta(number_years, 'XXX')
        print('Print ORCA Inputs: ' + file_name)
        self.make_daily_timeseries(number_years, '1/1/1950', '12/31/2099', 1950, first_leap, 'XXX', file_folder, file_name)

    def initialize_reservoirs(self):
        for x in self.reservoir_list:
            x.monthly = {}
            for data_type in self.data_type_list:
                x.monthly[data_type] = {}
                x.monthly[data_type]['flows'] = np.zeros((12, self.number_years))
                x.monthly[data_type]['coefficients'] = np.zeros((12, 2))
                x.monthly[data_type]['residuals'] = np.zeros((12, self.number_years))
                x.monthly[data_type]['whitened'] = np.zeros((12, self.number_years))
                x.monthly[data_type]['whitened_residuals'] = np.zeros((12, self.number_years))
                x.monthly[data_type]['AR_coef'] = np.zeros((12, 2))
                x.monthly[data_type]['AR_residuals'] = np.zeros((12, self.number_years))
                x.monthly[data_type]['white_mean'] = np.zeros(12)
                x.monthly[data_type]['white_std'] = np.zeros(12)
                x.monthly[data_type]['res_mean'] = np.zeros(12)
                x.monthly[data_type]['res_std'] = np.zeros(12)
                x.monthly[data_type]['hist_max'] = np.zeros(12)
                x.monthly[data_type]['hist_min'] = np.zeros(12)
                x.monthly[data_type]['baseline_value'] = np.zeros((12, self.number_years))
                x.monthly[data_type]['use_log'] = ['no' for i in range(0, 12)]

                x.monthly[data_type]['daily'] = {}
                monthcounter = 0
                for monthname in self.monthlist:
                    x.monthly[data_type]['daily'][monthname] = np.zeros(
                        (self.number_years, self.days_in_month[self.non_leap_year][monthcounter]))
                    monthcounter += 1
                x.snowpack = {}
                x.snowpack['max'] = np.zeros(self.number_years)
                x.snowpack['daily'] = np.zeros((self.number_years, 366))
                x.snowpack['coef'] = np.zeros(2)
                x.snowpack['residuals'] = np.zeros(self.number_years)
                x.snowpack['max_sorted'] = np.zeros(self.number_years)
                x.snowpack['sorted_index'] = np.zeros(self.number_years)

        self.monthly = {}
        for deltaname in self.delta_list:
            self.monthly[deltaname] = {}
            self.monthly[deltaname]['gains'] = np.zeros((12, self.number_years))
            self.monthly[deltaname]['fnf'] = np.zeros((12, self.number_years))
            self.monthly[deltaname]['coef'] = np.zeros((12, 2))
            self.monthly[deltaname]['residuals'] = np.zeros((12, self.number_years))
            self.monthly[deltaname]['whitened'] = np.zeros((12, self.number_years))
            self.monthly[deltaname]['whitened_fnf'] = np.zeros((12, self.number_years))
            self.monthly[deltaname]['whitened_residuals'] = np.zeros((12, self.number_years))
            self.monthly[deltaname]['AR_coef'] = np.zeros((12, 2))
            self.monthly[deltaname]['AR_residuals'] = np.zeros((12, self.number_years))
            self.monthly[deltaname]['white_mean'] = np.zeros(12)
            self.monthly[deltaname]['white_std'] = np.zeros(12)
            self.monthly[deltaname]['white_fnf_mean'] = np.zeros(12)
            self.monthly[deltaname]['white_fnf_std'] = np.zeros(12)
            self.monthly[deltaname]['res_mean'] = np.zeros(12)
            self.monthly[deltaname]['res_std'] = np.zeros(12)
            self.monthly[deltaname]['hist_max'] = np.zeros(12)
            self.monthly[deltaname]['hist_min'] = np.zeros(12)
            self.monthly[deltaname]['use_log'] = ['no' for i in range(0, 12)]
            self.monthly[deltaname]['baseline_value'] = np.zeros((12, self.number_years))
            self.monthly[deltaname]['daily'] = {}
            monthcounter = 0
            for monthname in self.monthlist:
                self.monthly[deltaname]['daily'][monthname] = np.zeros(
                    (self.number_years, self.days_in_month[self.non_leap_year][monthcounter]))
                monthcounter += 1

    def generate_relationships(self, plot_key):
        for t in range(0, self.T):
            m = self.month[t]
            da = self.day_month[t]
            wateryear = self.water_year[t]
            year = self.year[t] - self.starting_year

            if da == 29 and m == 2:
                da = 28
            for x in self.reservoir_list:
                x.monthly['fnf']['flows'][m - 1][wateryear] += x.fnf[t] * 1000.0
                x.monthly['inf']['flows'][m - 1][wateryear] += x.Q[t]
                x.monthly['gains']['flows'][m - 1][wateryear] += x.downstream[t]
                x.monthly['evap']['flows'][m - 1][wateryear] += x.E[t]
                x.monthly['precip']['flows'][m - 1][wateryear] += x.precip[t]
                x.monthly['fci']['flows'][m - 1][wateryear] += x.fci[t] / self.days_in_month[year][m - 1]
                x.monthly['otf']['flows'][m - 1][wateryear] += self.df['%s_otf' % x.key].iloc[t] * cfs_tafd

                x.monthly['fnf']['daily'][self.monthlist[m - 1]][wateryear][da - 1] += x.fnf[t] * 1000.0
                x.monthly['inf']['daily'][self.monthlist[m - 1]][wateryear][da - 1] += x.Q[t]
                x.monthly['gains']['daily'][self.monthlist[m - 1]][wateryear][da - 1] += x.downstream[t]
                x.monthly['evap']['daily'][self.monthlist[m - 1]][wateryear][da - 1] += x.E[t]
                x.monthly['precip']['daily'][self.monthlist[m - 1]][wateryear][da - 1] += x.precip[t]
                x.monthly['fci']['daily'][self.monthlist[m - 1]][wateryear][da - 1] += x.fci[t]
                x.monthly['otf']['daily'][self.monthlist[m - 1]][wateryear][da - 1] += self.df['%s_otf' % x.key].iloc[
                                                                                           t] * cfs_tafd

        for x in self.reservoir_list:
            for data_type in self.data_type_list:
                x.monthly[data_type]['sorted'] = np.zeros((12, self.number_years))
                x.monthly[data_type]['sort_index'] = np.zeros((12, self.number_years))
                monthcounter = 0
                for monthname in self.monthlist:
                    for wateryearnum in range(0, self.number_years):
                        if any(positive_nums > 0.0 for positive_nums in
                               x.monthly[data_type]['daily'][monthname][wateryearnum]) and any(
                                negative_nums < 0.0 for negative_nums in
                                x.monthly[data_type]['daily'][monthname][wateryearnum]):
                            if x.monthly[data_type]['flows'][monthcounter][wateryearnum] > 0.0:
                                x.monthly[data_type]['baseline_value'][monthcounter][wateryearnum] = np.min(
                                    x.monthly[data_type]['daily'][monthname][wateryearnum])
                            else:
                                x.monthly[data_type]['baseline_value'][monthcounter][wateryearnum] = np.max(
                                    x.monthly[data_type]['daily'][monthname][wateryearnum])
                        else:
                            x.monthly[data_type]['baseline_value'][monthcounter][wateryearnum] = 0.0
                        for daynum in range(0, len(x.monthly[data_type]['daily'][monthname][wateryearnum])):
                            if np.power(x.monthly[data_type]['flows'][monthcounter][wateryearnum], 2) > 0.0:
                                x.monthly[data_type]['daily'][monthname][wateryearnum][daynum] = (x.monthly[data_type][
                                                                                                 'daily'][monthname][
                                                                                                 wateryearnum][daynum] -
                                                                                             x.monthly[data_type][
                                                                                                 'baseline_value'][
                                                                                                 monthcounter][
                                                                                                 wateryearnum]) / (x.monthly[
                                                                                                                  data_type][
                                                                                                                  'flows'][
                                                                                                                  monthcounter][
                                                                                                                  wateryearnum] -
                                                                                                              x.monthly[
                                                                                                                  data_type][
                                                                                                                  'baseline_value'][
                                                                                                                  monthcounter][
                                                                                                                  wateryearnum] *
                                                                                                              self.days_in_month[wateryearnum+1][
                                                                                                                  monthcounter])
                    monthcounter += 1
                for monthcounter in range(0, 12):
                    x.monthly[data_type]['sorted'][monthcounter] = np.sort(x.monthly[data_type]['flows'][monthcounter])
                    x.monthly[data_type]['sort_index'][monthcounter] = np.argsort(
                        x.monthly[data_type]['flows'][monthcounter])
            snowmelt_fnf = np.zeros(self.number_years)
            for yearcounter in range(0, self.number_years):
                snowmelt_fnf[yearcounter] = x.monthly['fnf']['flows'][3][yearcounter] + x.monthly['fnf']['flows'][4][
                    yearcounter] + x.monthly['fnf']['flows'][5][yearcounter] + x.monthly['fnf']['flows'][6][yearcounter]

            x.monthly['snowmelt_sorted'] = np.sort(snowmelt_fnf)
            x.monthly['snowmelt_sort_index'] = np.argsort(snowmelt_fnf)

        for x in self.reservoir_list:
            for monthcounter in range(0, 12):
                # PLOTTING
                if plot_key == x.key:
                    fig = plt.figure()
                    type_counter = 1
                ##########
                for data_type in self.data_type_list:
                    # PLOTTING
                    if plot_key == x.key:
                        ax1 = fig.add_subplot(3, 2, type_counter)
                    ############
                    if data_type == 'fnf':
                        log_data = np.zeros(self.number_years)
                        for y in range(0, self.number_years):
                            if x.monthly[data_type]['flows'][monthcounter][y] > 0.0:
                                log_data[y] = np.log(x.monthly[data_type]['flows'][monthcounter][y])
                            else:
                                log_data[y] = 0.0
                        x.monthly[data_type]['use_log'][monthcounter] = 'yes'
                        x.monthly[data_type]['whitened'][monthcounter], x.monthly[data_type]['white_mean'][
                            monthcounter], x.monthly[data_type]['white_std'][monthcounter] = self.whiten_data(log_data)

                        # PLOTTING
                        if plot_key == x.key:
                            ax1.plot(x.monthly[data_type]['flows'][monthcounter])
                            ax1.set_xlabel("Year")
                            ax1.set_ylabel("Monthly FNF (tAF)")
                        ############

                    elif data_type == 'gains' or data_type == 'inf' or data_type == 'otf':
                        negative_counter = 0
                        for yy in range(0, len(x.monthly[data_type]['flows'][monthcounter])):
                            if x.monthly[data_type]['flows'][monthcounter][yy] <= 0.0:
                                negative_counter = 1
                        if negative_counter == 1:
                            x.monthly[data_type]['whitened'][monthcounter], x.monthly[data_type]['white_mean'][
                                monthcounter], x.monthly[data_type]['white_std'][monthcounter] = self.whiten_data(
                                x.monthly[data_type]['flows'][monthcounter])
                        else:
                            log_gains = np.zeros(len(x.monthly[data_type]['flows'][monthcounter]))
                            x.monthly[data_type]['use_log'][monthcounter] = 'yes'
                            for y in range(0, len(log_gains)):
                                log_gains[y] = np.log(x.monthly[data_type]['flows'][monthcounter][y])
                                x.monthly[data_type]['whitened'][monthcounter], x.monthly[data_type]['white_mean'][
                                    monthcounter], x.monthly[data_type]['white_std'][monthcounter] = self.whiten_data(
                                    log_gains)
                        x.monthly[data_type]['coefficients'][monthcounter], x.monthly[data_type]['residuals'][
                            monthcounter] = self.make_regression(x.monthly['fnf']['whitened'][monthcounter],
                                                                 x.monthly[data_type]['whitened'][monthcounter], 'yes')

                        # PLOTTING
                        if plot_key == x.key:
                            ax1.scatter(x.monthly['fnf']['whitened'][monthcounter],
                                        x.monthly[data_type]['whitened'][monthcounter], s=50, c='red', edgecolor='none',
                                        alpha=0.7)
                            ax1.plot([np.min(x.monthly['fnf']['whitened'][monthcounter]),
                                      np.max(x.monthly['fnf']['whitened'][monthcounter])], [
                                         x.monthly[data_type]['coefficients'][monthcounter][1] + np.min(
                                             x.monthly['fnf']['whitened'][monthcounter]) *
                                         x.monthly[data_type]['coefficients'][monthcounter][0],
                                         x.monthly[data_type]['coefficients'][monthcounter][1] + np.max(
                                             x.monthly['fnf']['whitened'][monthcounter]) *
                                         x.monthly[data_type]['coefficients'][monthcounter][0]])
                            ax1.set_xlabel("FNF SDs from Mean")
                            ax1.set_ylabel(data_type + " SDs from Mean")
                        ####################################

                    else:
                        x.monthly[data_type]['whitened'][monthcounter], x.monthly[data_type]['white_mean'][
                            monthcounter], x.monthly[data_type]['white_std'][monthcounter] = self.whiten_data(
                            x.monthly[data_type]['flows'][monthcounter])
                        x.monthly[data_type]['coefficients'][monthcounter], x.monthly[data_type]['residuals'][
                            monthcounter] = self.make_regression(x.monthly['fnf']['whitened'][monthcounter],
                                                                 x.monthly[data_type]['whitened'][monthcounter], 'yes')

                        # PLOTTING
                        if plot_key == x.key:
                            ax1.scatter(x.monthly['fnf']['whitened'][monthcounter],
                                        x.monthly[data_type]['whitened'][monthcounter], s=50, c='red', edgecolor='none',
                                        alpha=0.7)
                            ax1.plot([np.min(x.monthly['fnf']['whitened'][monthcounter]),
                                      np.max(x.monthly['fnf']['whitened'][monthcounter])], [
                                         x.monthly[data_type]['coefficients'][monthcounter][1] + np.min(
                                             x.monthly['fnf']['whitened'][monthcounter]) *
                                         x.monthly[data_type]['coefficients'][monthcounter][0],
                                         x.monthly[data_type]['coefficients'][monthcounter][1] + np.max(
                                             x.monthly['fnf']['whitened'][monthcounter]) *
                                         x.monthly[data_type]['coefficients'][monthcounter][0]])
                            ax1.set_xlabel("FNF SDs from Mean")
                            ax1.set_ylabel(data_type + " SDs from Mean")
                        ###################

                    x.monthly[data_type]['hist_max'][monthcounter] = np.max(
                        x.monthly[data_type]['whitened'][monthcounter])
                    x.monthly[data_type]['hist_min'][monthcounter] = np.min(
                        x.monthly[data_type]['whitened'][monthcounter])

                    x.monthly[data_type]['whitened_residuals'][monthcounter], x.monthly[data_type]['res_mean'][
                        monthcounter], x.monthly[data_type]['res_std'][monthcounter] = self.whiten_data(
                        x.monthly[data_type]['residuals'][monthcounter])
                    # PLOTTING
                    if plot_key == x.key:
                        type_counter += 1
                    ########
                # PLOTTING
                if plot_key == x.key:
                    fig.suptitle(x.key + ' ' + self.monthlist[monthcounter])
                    plt.show()
                    plt.close()
                ############

    def generate_relationships_delta(self, plot_key):
        for t in range(0, self.T):
            m = self.month[t]
            da = self.day_month[t]
            wateryear = self.water_year[t]
            if da == 29 and m == 2:
                da = 28

            self.monthly['SAC']['gains'][m - 1][wateryear] += self.df.SAC_gains[t] * cfs_tafd
            self.monthly['SJ']['gains'][m - 1][wateryear] += self.df.SJ_gains[t] * cfs_tafd
            self.monthly['EAST']['gains'][m - 1][wateryear] += self.df.EAST_gains[t] * cfs_tafd
            self.monthly['depletions']['gains'][m - 1][wateryear] += self.df.delta_depletions[t] * cfs_tafd
            self.monthly['CCC']['gains'][m - 1][wateryear] += self.df.CCC_pump[t] * cfs_tafd
            self.monthly['BRK']['gains'][m - 1][wateryear] += self.df.BRK_pump[t] * cfs_tafd

            self.monthly['SAC']['daily'][self.monthlist[m - 1]][wateryear][da - 1] += self.df.SAC_gains[t] * cfs_tafd
            self.monthly['SJ']['daily'][self.monthlist[m - 1]][wateryear][da - 1] += self.df.SJ_gains[t] * cfs_tafd
            self.monthly['EAST']['daily'][self.monthlist[m - 1]][wateryear][da - 1] += self.df.EAST_gains[t] * cfs_tafd
            self.monthly['depletions']['daily'][self.monthlist[m - 1]][wateryear][da - 1] += self.df.delta_depletions[
                                                                                                 t] * cfs_tafd
            self.monthly['CCC']['daily'][self.monthlist[m - 1]][wateryear][da - 1] += self.df.CCC_pump[t] * cfs_tafd
            self.monthly['BRK']['daily'][self.monthlist[m - 1]][wateryear][da - 1] += self.df.BRK_pump[t] * cfs_tafd

        for deltaname in self.delta_list:
            monthcounter = 0
            self.monthly[deltaname]['sorted'] = np.zeros((12, self.number_years))
            self.monthly[deltaname]['sort_index'] = np.zeros((12, self.number_years))
            for monthname in self.monthlist:
                for wateryearnum in range(0, self.number_years):
                    if any(positive_nums > 0.0 for positive_nums in
                           self.monthly[deltaname]['daily'][monthname][wateryearnum]) and any(
                            negative_nums < 0.0 for negative_nums in
                            self.monthly[deltaname]['daily'][monthname][wateryearnum]):
                        if self.monthly[deltaname]['gains'][monthcounter][wateryearnum] > 0.0:
                            self.monthly[deltaname]['baseline_value'][monthcounter][wateryearnum] = np.min(
                                self.monthly[deltaname]['daily'][monthname][wateryearnum])
                        else:
                            self.monthly[deltaname]['baseline_value'][monthcounter][wateryearnum] = np.max(
                                self.monthly[deltaname]['daily'][monthname][wateryearnum])
                    else:
                        self.monthly[deltaname]['baseline_value'][monthcounter][wateryearnum] = 0.0
                    for daynum in range(0, len(self.monthly[deltaname]['daily'][monthname][wateryearnum])):
                        if np.power(self.monthly[deltaname]['gains'][monthcounter][wateryearnum], 2) > 0.0:
                            self.monthly[deltaname]['daily'][monthname][wateryearnum][daynum] = (self.monthly[deltaname][
                                                                                                'daily'][monthname][
                                                                                                wateryearnum][daynum] -
                                                                                            self.monthly[deltaname][
                                                                                                'baseline_value'][
                                                                                                monthcounter][
                                                                                                wateryearnum]) / (
                                                                                                       self.monthly[
                                                                                                           deltaname][
                                                                                                           'gains'][
                                                                                                           monthcounter][
                                                                                                           wateryearnum] -
                                                                                                       self.monthly[
                                                                                                           deltaname][
                                                                                                           'baseline_value'][
                                                                                                           monthcounter][
                                                                                                           wateryearnum] *
                                                                                                       self.days_in_month[wateryearnum+1][
                                                                                                           monthcounter])
                monthcounter += 1
            for monthcounter in range(0, 12):
                self.monthly[deltaname]['sorted'][monthcounter] = np.sort(
                    self.monthly[deltaname]['gains'][monthcounter])
                self.monthly[deltaname]['sort_index'][monthcounter] = np.argsort(
                    self.monthly[deltaname]['gains'][monthcounter])

        for monthcounter in range(0, 12):
            for yearcounter in range(0, self.number_years):
                for reservoir in [self.shasta, self.oroville, self.yuba, self.folsom]:
                    self.monthly['SAC']['fnf'][monthcounter][yearcounter] += \
                    reservoir.monthly['fnf']['flows'][monthcounter][yearcounter]
                    self.monthly['CCC']['fnf'][monthcounter][yearcounter] += \
                    reservoir.monthly['fnf']['flows'][monthcounter][yearcounter]
                    self.monthly['BRK']['fnf'][monthcounter][yearcounter] += \
                    reservoir.monthly['fnf']['flows'][monthcounter][yearcounter]

                for reservoir in [self.newmelones, self.donpedro, self.exchequer, self.millerton]:
                    self.monthly['SJ']['fnf'][monthcounter][yearcounter] += \
                    reservoir.monthly['fnf']['flows'][monthcounter][yearcounter]

                for reservoir in [self.shasta, self.oroville, self.yuba, self.folsom, self.newmelones, self.donpedro,
                                  self.exchequer, self.millerton]:
                    self.monthly['EAST']['fnf'][monthcounter][yearcounter] += \
                    reservoir.monthly['fnf']['flows'][monthcounter][yearcounter]
                    self.monthly['depletions']['fnf'][monthcounter][yearcounter] += \
                    reservoir.monthly['fnf']['flows'][monthcounter][yearcounter]

        # for deltaname in self.delta_list:
        # self.monthly[deltaname]['sorted'] = np.zeros((12, self.number_years))
        # self.monthly[deltaname]['sorted_index'] = np.zeros((12, self.number_years))
        # for monthcounter in range(0,12):
        # self.monthly[deltaname]['sorted'][monthcounter] = np.sort(self.monthly[deltaname]['fnf'][monthcounter])
        # self.monthly[deltaname]['sorted_index'][monthcounter] = np.argsort(self.monthly[deltaname]['fnf'][monthcounter])

        # PLOTTING
        for deltaname in self.delta_list:
            if plot_key == deltaname:
                fig = plt.figure()
                gs = gridspec.GridSpec(5, 3)
            ##########
            for monthcounter in range(0, 12):

                negative_counter = 0
                for yy in range(0, len(self.monthly[deltaname]['gains'][monthcounter])):
                    if self.monthly[deltaname]['gains'][monthcounter][yy] <= 0.0:
                        negative_counter = 1
                if negative_counter == 1:
                    self.monthly[deltaname]['use_log'][monthcounter] = 'no'
                    self.monthly[deltaname]['whitened'][monthcounter], self.monthly[deltaname]['white_mean'][
                        monthcounter], self.monthly[deltaname]['white_std'][monthcounter] = self.whiten_data(
                        self.monthly[deltaname]['gains'][monthcounter])
                else:
                    self.monthly[deltaname]['use_log'][monthcounter] = 'yes'
                    log_gains = np.zeros(len(self.monthly[deltaname]['gains'][monthcounter]))
                    for y in range(0, len(log_gains)):
                        log_gains[y] = np.log(self.monthly[deltaname]['gains'][monthcounter][y])
                    self.monthly[deltaname]['whitened'][monthcounter], self.monthly[deltaname]['white_mean'][
                        monthcounter], self.monthly[deltaname]['white_std'][monthcounter] = self.whiten_data(log_gains)
                log_fnf = np.zeros(len(self.monthly[deltaname]['fnf'][monthcounter]))
                for yy in range(0, len(self.monthly[deltaname]['fnf'][monthcounter])):
                    if self.monthly[deltaname]['fnf'][monthcounter][yy] > 0.0:
                        log_fnf[yy] = np.log(self.monthly[deltaname]['fnf'][monthcounter][yy])
                    else:
                        log_fnf[yy] = 0.0
                self.monthly[deltaname]['whitened_fnf'][monthcounter], self.monthly[deltaname]['white_fnf_mean'][
                    monthcounter], self.monthly[deltaname]['white_fnf_std'][monthcounter] = self.whiten_data(log_fnf)
                self.monthly[deltaname]['coef'][monthcounter], self.monthly[deltaname]['residuals'][
                    monthcounter] = self.make_regression(self.monthly[deltaname]['whitened_fnf'][monthcounter],
                                                         self.monthly[deltaname]['whitened'][monthcounter], 'yes')

                self.monthly[deltaname]['hist_max'][monthcounter] = np.max(
                    self.monthly[deltaname]['whitened'][monthcounter])
                self.monthly[deltaname]['hist_min'][monthcounter] = np.min(
                    self.monthly[deltaname]['whitened'][monthcounter])

                # PLOTTING
                if plot_key == deltaname:
                    if monthcounter < 4:
                        ax1 = plt.subplot(gs[monthcounter + 1, 0])
                    elif monthcounter < 8:
                        ax1 = plt.subplot(gs[monthcounter - 3, 1])
                    else:
                        ax1 = plt.subplot(gs[monthcounter - 7, 2])

                    ax1.scatter(whitened_fnf, self.monthly[deltaname]['whitened'][monthcounter], s=50, c='red',
                                edgecolor='none', alpha=0.7)
                    ax1.plot([np.min(whitened_fnf), np.max(whitened_fnf)], [
                        self.monthly[deltaname]['coef'][monthcounter][1] + np.min(whitened_fnf) *
                        self.monthly[deltaname]['coef'][monthcounter][0],
                        self.monthly[deltaname]['coef'][monthcounter][1] + np.max(whitened_fnf) *
                        self.monthly[deltaname]['coef'][monthcounter][0]])
                    ax1.set_xlabel(self.monthlist[monthcounter] + " FNF")
                    ax1.set_ylabel(self.monthlist[monthcounter] + deltaname)
                ####################################

                self.monthly[deltaname]['whitened_residuals'][monthcounter], self.monthly[deltaname]['res_mean'][
                    monthcounter], self.monthly[deltaname]['res_std'][monthcounter] = self.whiten_data(
                    self.monthly[deltaname]['residuals'][monthcounter])
            if plot_key == deltaname:
                single_timeseries = self.unfold_series(self.monthly[deltaname]['gains'], 10)
                ax1 = plt.subplot(gs[0, :])
                ax1.plot(single_timeseries, color='black', linewidth=2)
                ax1.set_ylabel(deltaname + ' flow')
                ax1.set_xlabel('Timeseries')
                fig.suptitle(deltaname)
                plt.show()
                plt.close()

            ############

    def autocorrelate_residuals(self, plot_key):
        for x in self.reservoir_list:
            for data_type in self.data_type_list:
                # PLOTTING
                if plot_key == x.key:
                    fig = plt.figure()
                    gs = gridspec.GridSpec(5, 3)
                #########
                for monthcounter in range(0, 12):
                    # PLOTTING
                    if plot_key == x.key:
                        if monthcounter < 4:
                            ax1 = plt.subplot(gs[monthcounter + 1, 0])
                        elif monthcounter < 8:
                            ax1 = plt.subplot(gs[monthcounter - 3, 1])
                        else:
                            ax1 = plt.subplot(gs[monthcounter - 7, 2])
                    ############
                    if monthcounter == 0:
                        prevmonthcounter = 11
                        this_month_res = x.monthly[data_type]['whitened_residuals'][monthcounter]
                        prev_month_res = x.monthly[data_type]['whitened_residuals'][prevmonthcounter]
                    elif monthcounter == 10:
                        prevmonthcounter = monthcounter - 1
                        this_month_res = np.zeros(len(x.monthly[data_type]['whitened_residuals'][monthcounter]) - 1)
                        prev_month_res = np.zeros(len(x.monthly[data_type]['whitened_residuals'][monthcounter]) - 1)
                        for yy in range(0, len(this_month_res)):
                            this_month_res[yy] = x.monthly[data_type]['whitened_residuals'][monthcounter][yy + 1]
                            prev_month_res[yy] = x.monthly[data_type]['whitened_residuals'][prevmonthcounter][yy]
                    else:
                        prevmonthcounter = monthcounter - 1
                        this_month_res = x.monthly[data_type]['whitened_residuals'][monthcounter]
                        prev_month_res = x.monthly[data_type]['whitened_residuals'][prevmonthcounter]
                    x.monthly[data_type]['AR_coef'][monthcounter], x.monthly[data_type]['AR_residuals'][monthcounter][
                                                                   0:len(this_month_res)] = self.make_regression(
                        prev_month_res, this_month_res, 'yes')

                    # PLOTTING
                    if plot_key == x.key:
                        ax1.scatter(prev_month_res, this_month_res, s=50, c='red', edgecolor='none', alpha=0.7)
                        ax1.plot([np.min(prev_month_res), np.max(prev_month_res)], [
                            x.monthly[data_type]['AR_coef'][monthcounter][1] + np.min(prev_month_res) *
                            x.monthly[data_type]['AR_coef'][monthcounter][0],
                            x.monthly[data_type]['AR_coef'][monthcounter][1] + np.max(prev_month_res) *
                            x.monthly[data_type]['AR_coef'][monthcounter][0]])
                        ax1.set_xlabel(self.monthlist[prevmonthcounter])
                        ax1.set_ylabel(self.monthlist[monthcounter])
                    ##############
                # PLOTTING
                if plot_key == x.key:
                    single_timeseries = self.unfold_series(x.monthly[data_type]['whitened_residuals'], 10)
                    autoregressive_timeseries = np.zeros(len(single_timeseries))
                    autoregressive_timeseries[0] = single_timeseries[0]
                    month_index = 10
                    year_index = 0
                    for regression_steps in range(1, len(single_timeseries)):
                        autoregressive_timeseries[regression_steps] = \
                        x.monthly[data_type]['whitened_residuals'][month_index][year_index] * \
                        x.monthly[data_type]['AR_coef'][month_index][0] + x.monthly[data_type]['AR_coef'][month_index][
                            1]
                        month_index += 1
                        if month_index == 12:
                            month_index = 0
                        if month_index == 10:
                            year_index += 1
                    ax1 = plt.subplot(gs[0, :])
                    ax1.plot(single_timeseries, color='black', linewidth=2)
                    ax1.plot(autoregressive_timeseries, color='red', linewidth=2)
                    ax1.set_ylabel('FNF Regression Residuals')
                    ax1.set_xlabel('Timeseries')
                    fig.suptitle(x.key + ' ' + data_type)
                    plt.show()
                    plt.close()

    def autocorrelate_residuals_delta(self, plot_key):
        for deltaname in self.delta_list:
            # PLOTTING
            if plot_key == deltaname:
                fig = plt.figure()
                gs = gridspec.GridSpec(5, 3)
            #########
            for monthcounter in range(0, 12):
                # PLOTTING
                if plot_key == deltaname:
                    if monthcounter < 4:
                        ax1 = plt.subplot(gs[monthcounter + 1, 0])
                    elif monthcounter < 8:
                        ax1 = plt.subplot(gs[monthcounter - 3, 1])
                    else:
                        ax1 = plt.subplot(gs[monthcounter - 7, 2])
                ############
                if monthcounter == 0:
                    prevmonthcounter = 11
                    this_month_res = self.monthly[deltaname]['whitened_residuals'][monthcounter]
                    prev_month_res = self.monthly[deltaname]['whitened_residuals'][prevmonthcounter]
                elif monthcounter == 10:
                    prevmonthcounter = monthcounter - 1
                    this_month_res = np.zeros(len(self.monthly[deltaname]['whitened_residuals'][monthcounter]) - 1)
                    prev_month_res = np.zeros(len(self.monthly[deltaname]['whitened_residuals'][monthcounter]) - 1)
                    for yy in range(0, len(this_month_res)):
                        this_month_res[yy] = self.monthly[deltaname]['whitened_residuals'][monthcounter][yy + 1]
                        prev_month_res[yy] = self.monthly[deltaname]['whitened_residuals'][prevmonthcounter][yy]
                else:
                    prevmonthcounter = monthcounter - 1
                    this_month_res = self.monthly[deltaname]['whitened_residuals'][monthcounter]
                    prev_month_res = self.monthly[deltaname]['whitened_residuals'][prevmonthcounter]
                self.monthly[deltaname]['AR_coef'][monthcounter], self.monthly[deltaname]['AR_residuals'][monthcounter][
                                                                  0:len(this_month_res)] = self.make_regression(
                    prev_month_res, this_month_res, 'yes')

                # PLOTTING
                if plot_key == deltaname:
                    ax1.scatter(prev_month_res, this_month_res, s=50, c='red', edgecolor='none', alpha=0.7)
                    ax1.plot([np.min(prev_month_res), np.max(prev_month_res)], [
                        self.monthly[deltaname]['AR_coef'][monthcounter][1] + np.min(prev_month_res) *
                        self.monthly[deltaname]['AR_coef'][monthcounter][0],
                        self.monthly[deltaname]['AR_coef'][monthcounter][1] + np.max(prev_month_res) *
                        self.monthly[deltaname]['AR_coef'][monthcounter][0]])
                    ax1.set_xlabel(self.monthlist[prevmonthcounter])
                    ax1.set_ylabel(self.monthlist[monthcounter])
                    ##############
            # PLOTTING
            if plot_key == deltaname:
                single_timeseries = self.unfold_series(self.monthly[deltaname]['whitened_residuals'], 10)
                autoregressive_timeseries = np.zeros(len(single_timeseries))
                autoregressive_timeseries[0] = single_timeseries[0]
                month_index = 10
                year_index = 0
                for regression_steps in range(1, len(single_timeseries)):
                    autoregressive_timeseries[regression_steps] = \
                    self.monthly[deltaname]['whitened_residuals'][month_index][year_index] * \
                    self.monthly[deltaname]['AR_coef'][month_index][0] + \
                    self.monthly[deltaname]['AR_coef'][month_index][1]
                    month_index += 1
                    if month_index == 12:
                        month_index = 0
                    if month_index == 10:
                        year_index += 1
                ax1 = plt.subplot(gs[0, :])
                ax1.plot(single_timeseries, color='black', linewidth=2)
                ax1.plot(autoregressive_timeseries, color='red', linewidth=2)
                ax1.set_ylabel('FNF Regression Residuals')
                ax1.set_xlabel('Timeseries')
                fig.suptitle(deltaname)
                plt.show()
                plt.close()

    def fill_snowpack(self, plot_key):
        for t in range(0, self.T):
            dowy = self.dowy[t]
            wateryear = self.water_year[t]

            for x in self.reservoir_list:
                x.snowpack['max'][wateryear] = max(x.SNPK[t], x.snowpack['max'][wateryear])
                x.snowpack['daily'][wateryear][dowy] = x.SNPK[t]

        for x in self.reservoir_list:
            for yearcounter in range(0, self.number_years):
                for daycount in range(0, 366):
                    if x.snowpack['max'][yearcounter] > 0.0:
                        x.snowpack['daily'][yearcounter][daycount] = x.snowpack['daily'][yearcounter][daycount] / \
                                                                     x.snowpack['max'][yearcounter]
            melt_fnf = np.zeros(self.number_years)
            for y in range(0, self.number_years):
                for snowmelt in range(3, 7):
                    melt_fnf[y] += x.monthly['fnf']['flows'][snowmelt][y]

            x.snowpack['coef'], x.snowpack['residuals'] = self.make_regression(melt_fnf, x.snowpack['max'], 'yes')
            if plot_key == x.key:
                fig = plt.figure()
                gs = gridspec.GridSpec(2, 2)
                ax1 = plt.subplot(gs[0, 0])
                ax1.plot(melt_fnf)
                ax1.set_ylabel('Total Melt FNF')
                ax1.set_xlabel('Year')
                ax1 = plt.subplot(gs[0, 1])
                ax1.plot(x.snowpack['max'])
                ax1.set_ylabel('Max Snowpack')
                ax1.set_xlabel('Year')
                ax1 = plt.subplot(gs[1, 0])
                ax1.scatter(melt_fnf, x.snowpack['max'], s=50, c='red', edgecolor='none', alpha=0.7)
                ax1.plot([np.min(melt_fnf), np.max(melt_fnf)],
                         [(np.min(melt_fnf) * x.snowpack['coef'][0] + x.snowpack['coef'][1]),
                          (np.max(melt_fnf) * x.snowpack['coef'][0] + x.snowpack['coef'][1])])
                ax1.set_ylabel('Snowpack')
                ax1.set_xlabel('FNF')
                ax1 = plt.subplot(gs[1, 1])
                for yearcount in range(0, self.number_years):
                    ax1.plot(x.snowpack['daily'][yearcount])
                ax1.set_ylabel('Snowpack Fraction')
                ax1.set_xlabel('DOWY')
                fig.suptitle(x.key + ' Snowpack')
                plt.tight_layout()
                plt.show()
                plt.close()

    def read_new_fnf_data(self, filename, timestep_length, start_month, first_leap_year, numYears):
        monthcount = start_month - 1
        daycount = 0
        yearcount = 0
        thismonthday = np.where(first_leap_year == 0, self.days_in_month[self.leap_year][monthcount],
                                self.days_in_month[self.non_leap_year][monthcount])
        leapcount = 0
        self.fnf_df = pd.read_csv(filename)
        for reservoir in self.reservoir_list:
            reservoir.fnf_new = self.fnf_df['%s_fnf' % reservoir.key].values * cfs_tafd
            reservoir.monthly_new = {}
            reservoir.snowpack['new_melt_fnf'] = np.zeros(numYears)
            for data_type in self.data_type_list:
                reservoir.monthly_new[data_type] = {}
                reservoir.monthly_new[data_type]['flows'] = np.zeros((12, numYears))
                reservoir.monthly_new[data_type]['whitened'] = np.zeros((12, numYears))
        for t in range(0, len(reservoir.fnf_new)):
            for reservoir in self.reservoir_list:
                if not np.isnan(reservoir.fnf_new[t]):
                    reservoir.monthly_new['fnf']['flows'][monthcount][yearcount] += reservoir.fnf_new[t]
                    if monthcount > 2 and monthcount < 7:
                        reservoir.snowpack['new_melt_fnf'][yearcount] += reservoir.fnf_new[t]
            daycount += 1
            if daycount == thismonthday:
                daycount = 0
                monthcount += 1
                if monthcount == 12:
                    monthcount = 0
                    yearcount += 1
                    leapcount += 1
                    if leapcount == 4:
                        leapcount = 0
                if leapcount == first_leap_year:
                    thismonthday = self.days_in_month[self.leap_year][monthcount]
                else:
                    thismonthday = self.days_in_month[self.non_leap_year][monthcount]

        self.monthly_new = {}
        for deltaname in self.delta_list:
            self.monthly_new[deltaname] = {}
            self.monthly_new[deltaname]['fnf'] = np.zeros((12, numYears))
            self.monthly_new[deltaname]['whitened_fnf'] = np.zeros((12, numYears))
            self.monthly_new[deltaname]['whitened'] = np.zeros((12, numYears))
            self.monthly_new[deltaname]['gains'] = np.zeros((12, numYears))

        for monthcounter in range(0, 12):
            for yearcounter in range(0, numYears):
                for reservoir in [self.shasta, self.oroville, self.yuba, self.folsom]:
                    self.monthly_new['SAC']['fnf'][monthcounter][yearcounter] += \
                    reservoir.monthly_new['fnf']['flows'][monthcounter][yearcounter]
                    self.monthly_new['CCC']['fnf'][monthcounter][yearcounter] += \
                    reservoir.monthly_new['fnf']['flows'][monthcounter][yearcounter]
                    self.monthly_new['BRK']['fnf'][monthcounter][yearcounter] += \
                    reservoir.monthly_new['fnf']['flows'][monthcounter][yearcounter]

                for reservoir in [self.newmelones, self.donpedro, self.exchequer, self.millerton]:
                    self.monthly_new['SJ']['fnf'][monthcounter][yearcounter] += \
                    reservoir.monthly_new['fnf']['flows'][monthcounter][yearcounter]

                for reservoir in [self.shasta, self.oroville, self.yuba, self.folsom, self.newmelones, self.donpedro,
                                  self.exchequer, self.millerton]:
                    self.monthly_new['EAST']['fnf'][monthcounter][yearcounter] += \
                    reservoir.monthly_new['fnf']['flows'][monthcounter][yearcounter]
                    self.monthly_new['depletions']['fnf'][monthcounter][yearcounter] += \
                    reservoir.monthly_new['fnf']['flows'][monthcounter][yearcounter]

    def whiten_by_historical_moments(self, numYears, plot_key):
        for reservoir in self.reservoir_list:
            if plot_key == reservoir.key:
                fig = plt.figure()
                gs = gridspec.GridSpec(12, 2)
            for monthcounter in range(0, 12):
                for yearcounter in range(0, numYears):
                    if reservoir.monthly['fnf']['use_log'][monthcounter] == 'yes':
                        if reservoir.monthly_new['fnf']['flows'][monthcounter][yearcounter] > 0.0:
                            log_data = np.log(reservoir.monthly_new['fnf']['flows'][monthcounter][yearcounter])
                        else:
                            log_data = 0.0
                        reservoir.monthly_new['fnf']['whitened'][monthcounter][yearcounter] = (log_data -
                                                                                               reservoir.monthly['fnf'][
                                                                                                   'white_mean'][
                                                                                                   monthcounter]) / \
                                                                                              reservoir.monthly['fnf'][
                                                                                                  'white_std'][
                                                                                                  monthcounter]
                    else:
                        non_log_data = reservoir.monthly_new['fnf']['flows'][monthcounter][yearcounter]
                        reservoir.monthly_new['fnf']['whitened'][monthcounter][yearcounter] = (non_log_data -
                                                                                               reservoir.monthly['fnf'][
                                                                                                   'white_mean'][
                                                                                                   monthcounter]) / \
                                                                                              reservoir.monthly['fnf'][
                                                                                                  'white_std'][
                                                                                                  monthcounter]
                if plot_key == reservoir.key:
                    ax1 = plt.subplot(gs[monthcounter, 0])
                    ax1.plot(reservoir.monthly_new['fnf']['flows'][monthcounter])
                    ax1.set_ylabel(self.monthlist[monthcounter])
                    if monthcounter == 0:
                        ax1.set_title('FNF')
                    ax1 = plt.subplot(gs[monthcounter, 1])
                    ax1.plot(reservoir.monthly_new['fnf']['whitened'][monthcounter])
                    if monthcounter == 0:
                        ax1.set_title('SDs from hist mean')
            if plot_key == reservoir.key:
                fig.suptitle(reservoir.key)
                plt.show()
                plt.close()

    def whiten_by_historical_moments_delta(self, numYears, plot_key):
        for deltaname in self.delta_list:
            # PLOTTING
            if deltaname == plot_key:
                fig = plt.figure()
                gs = gridspec.GridSpec(12, 2)
            ###########
            for monthcounter in range(0, 12):
                for yearcounter in range(0, numYears):
                    if self.monthly_new[deltaname]['fnf'][monthcounter][yearcounter] > 0.0:
                        log_data = np.log(self.monthly_new[deltaname]['fnf'][monthcounter][yearcounter])
                    else:
                        log_data = 0.0
                    self.monthly_new[deltaname]['whitened_fnf'][monthcounter][yearcounter] = (log_data -
                                                                                              self.monthly[deltaname][
                                                                                                  'white_fnf_mean'][
                                                                                                  monthcounter]) / \
                                                                                             self.monthly[deltaname][
                                                                                                 'white_fnf_std'][
                                                                                                 monthcounter]
                # PLOTTING
                if plot_key == deltaname:
                    ax1 = plt.subplot(gs[monthcounter, 0])
                    ax1.plot(self.monthly_new[deltaname]['fnf'][monthcounter])
                    ax1.set_ylabel(self.monthlist[monthcounter])
                    if monthcounter == 0:
                        ax1.set_title('FNF')
                    ax1 = plt.subplot(gs[monthcounter, 1])
                    ax1.plot(self.monthly_new[deltaname]['whitened_fnf'][monthcounter])
                    if monthcounter == 0:
                        ax1.set_title('SDs from hist mean')
            ##PLOTTING
            if plot_key == deltaname:
                fig.suptitle(deltaname)
                plt.show()
                plt.close()

    def make_fnf_prediction(self, numYears, plot_key):
        for reservoir in self.reservoir_list:
            reservoir.snowpack['pred_max'] = np.zeros(numYears)
            for wateryearnum in range(0, numYears):
                reservoir.snowpack['pred_max'][wateryearnum] = reservoir.snowpack['coef'][1] + reservoir.snowpack['coef'][
                    0] * reservoir.snowpack['new_melt_fnf'][wateryearnum]
            if plot_key == reservoir.key:
                fig = plt.figure()
                gs = gridspec.GridSpec(2, 1)
                ax1 = plt.subplot(gs[0, 0])
                ax1.plot(reservoir.snowpack['pred_max'])
                ax2 = plt.subplot(gs[1, 0])
                ax2.plot(reservoir.snowpack['new_melt_fnf'])
                fig.suptitle(reservoir.key)
                plt.show()
                plt.close()
            for data_type in self.data_type_list:
                if plot_key == reservoir.key:
                    fig = plt.figure()
                    gs = gridspec.GridSpec(12, 2)
                if data_type == 'fnf':
                    a = 1
                else:
                    for monthcounter in range(0, 12):
                        for yearcounter in range(0, numYears):
                            predictor = reservoir.monthly_new['fnf']['whitened'][monthcounter][yearcounter]
                            reservoir.monthly_new[data_type]['whitened'][monthcounter][yearcounter] = \
                            reservoir.monthly[data_type]['coefficients'][monthcounter][1] + \
                            reservoir.monthly[data_type]['coefficients'][monthcounter][0] * predictor

                if plot_key == reservoir.key:
                    for monthcounter in range(0, 12):
                        ax1 = plt.subplot(gs[monthcounter, 0])
                        ax1.plot(reservoir.monthly_new[data_type]['whitened'][monthcounter])
                        ax1.set_ylabel(self.monthlist[monthcounter])
                        if monthcounter == 0:
                            ax1.set_title(data_type)
                        ax1 = plt.subplot(gs[monthcounter, 1])
                        ax1.plot(reservoir.monthly_new['fnf']['whitened'][monthcounter])
                        if monthcounter == 0:
                            ax1.set_title('FNF')
                if plot_key == reservoir.key:
                    fig.suptitle(reservoir.key)
                    plt.show()
                    plt.close()

    def make_fnf_prediction_delta(self, numYears, plot_key):
        for deltaname in self.delta_list:
            # PLOTTING
            if plot_key == deltaname:
                fig = plt.figure()
                gs = gridspec.GridSpec(12, 2)
            #########
            for monthcounter in range(0, 12):
                for yearcounter in range(0, numYears):
                    predictor = self.monthly_new[deltaname]['whitened_fnf'][monthcounter][yearcounter]
                    self.monthly_new[deltaname]['whitened'][monthcounter][yearcounter] = \
                    self.monthly[deltaname]['coef'][monthcounter][1] + self.monthly[deltaname]['coef'][monthcounter][
                        0] * predictor

            # PLOTTING
            if plot_key == deltaname:
                for monthcounter in range(0, 12):
                    ax1 = plt.subplot(gs[monthcounter, 0])
                    ax1.plot(self.monthly_new[deltaname]['whitened'][monthcounter])
                    ax1.set_ylabel(self.monthlist[monthcounter])
                    if monthcounter == 0:
                        ax1.set_title(deltaname)
                    ax1 = plt.subplot(gs[monthcounter, 1])
                    ax1.plot(self.monthly_new[deltaname]['whitened_fnf'][monthcounter])
                    if monthcounter == 0:
                        ax1.set_title('FNF')
                fig.suptitle(deltaname)
                plt.show()
                plt.close()

    def find_residuals(self, start_month, numYears, plot_key):
        for reservoir in self.reservoir_list:
            for data_type in self.data_type_list:
                if plot_key == reservoir.key:
                    fig = plt.figure()
                reservoir.monthly_new[data_type]['whitened_residuals'] = np.zeros((12, numYears))
                random_start_integer = np.random.randint(
                    len(reservoir.monthly[data_type]['whitened_residuals'][start_month - 1]))
                prev_residual = reservoir.monthly[data_type]['whitened_residuals'][start_month - 1][
                    random_start_integer]
                for yearcount in range(0, numYears):
                    for monthcount in range(0, 12):
                        current_month = monthcount + start_month - 1
                        if current_month >= 12:
                            current_month -= 12
                        new_residual = reservoir.monthly[data_type]['AR_coef'][current_month][0] * prev_residual + \
                                       reservoir.monthly[data_type]['AR_coef'][current_month][1]
                        random_int = np.random.randint(len(reservoir.monthly[data_type]['AR_residuals'][current_month]))
                        ar_residual = reservoir.monthly[data_type]['AR_residuals'][current_month][random_int]
                        reservoir.monthly_new[data_type]['whitened_residuals'][current_month][
                            yearcount] = new_residual + ar_residual
                        prev_residual = new_residual + ar_residual
                if plot_key == reservoir.key:
                    for monthcounter in range(0, 12):
                        ax1 = fig.add_subplot(6, 2, monthcounter + 1)
                        ax1.plot(reservoir.monthly_new[data_type]['whitened_residuals'][monthcounter])
                        ax1.set_ylabel(self.monthlist[monthcounter])
                    fig.suptitle(reservoir.key + " " + data_type)
                    plt.show()
                    plt.close()

    def find_residuals_delta(self, start_month, numYears, plot_key):
        for deltaname in self.delta_list:
            ##PLOTTING
            if plot_key == deltaname:
                fig = plt.figure()
            ##########
            self.monthly_new[deltaname]['whitened_residuals'] = np.zeros((12, numYears))
            random_start_integer = np.random.randint(
                len(self.monthly[deltaname]['whitened_residuals'][start_month - 1]))
            prev_residual = self.monthly[deltaname]['whitened_residuals'][start_month - 1][random_start_integer]
            for yearcount in range(0, numYears):
                for monthcount in range(0, 12):
                    current_month = monthcount + start_month - 1
                    if current_month >= 12:
                        current_month -= 12
                    new_residual = self.monthly[deltaname]['AR_coef'][current_month][0] * prev_residual + \
                                   self.monthly[deltaname]['AR_coef'][current_month][1]
                    random_int = np.random.randint(len(self.monthly[deltaname]['AR_residuals'][current_month]))
                    ar_residual = self.monthly[deltaname]['AR_residuals'][current_month][random_int]
                    self.monthly_new[deltaname]['whitened_residuals'][current_month][
                        yearcount] = new_residual + ar_residual
                    prev_residual = new_residual + ar_residual
            # PLOTTING
            if plot_key == deltaname:
                for monthcounter in range(0, 12):
                    ax1 = fig.add_subplot(6, 2, monthcounter + 1)
                    ax1.plot(self.monthly_new[deltaname]['whitened_residuals'][monthcounter])
                    ax1.set_ylabel(self.monthlist[monthcounter])
                fig.suptitle(deltaname)
                plt.show()
                plt.close()

    def add_error(self, numYears, plot_key):
        for reservoir in self.reservoir_list:
            for data_type in self.data_type_list:
                for monthcounter in range(0, 12):
                    for yearcounter in range(0, numYears):
                        reservoir.monthly_new[data_type]['whitened'][monthcounter][yearcounter] += \
                        reservoir.monthly_new[data_type]['whitened_residuals'][monthcounter][yearcounter] * \
                        reservoir.monthly[data_type]['res_std'][monthcounter] + \
                        reservoir.monthly[data_type]['res_mean'][monthcounter]

                        if reservoir.monthly[data_type]['use_log'][monthcounter] == 'no':
                            if reservoir.monthly_new[data_type]['whitened'][monthcounter][yearcounter] > \
                                    reservoir.monthly[data_type]['hist_max'][monthcounter]:
                                reservoir.monthly_new[data_type]['whitened'][monthcounter][yearcounter] = \
                                reservoir.monthly[data_type]['hist_max'][monthcounter]
                            elif reservoir.monthly_new[data_type]['whitened'][monthcounter][yearcounter] < \
                                    reservoir.monthly[data_type]['hist_min'][monthcounter]:
                                reservoir.monthly_new[data_type]['whitened'][monthcounter][yearcounter] = \
                                reservoir.monthly[data_type]['hist_min'][monthcounter]

                        if data_type == 'fnf':
                            reservoir.monthly_new[data_type]['flows'][monthcounter][yearcounter] = \
                            reservoir.monthly_new[data_type]['flows'][monthcounter][yearcounter]
                        elif reservoir.monthly[data_type]['use_log'][monthcounter] == 'yes':
                            reservoir.monthly_new[data_type]['flows'][monthcounter][yearcounter] = np.exp(
                                reservoir.monthly_new[data_type]['whitened'][monthcounter][yearcounter] *
                                reservoir.monthly[data_type]['white_std'][monthcounter] +
                                reservoir.monthly[data_type]['white_mean'][monthcounter])
                        else:
                            reservoir.monthly_new[data_type]['flows'][monthcounter][yearcounter] = \
                            reservoir.monthly_new[data_type]['whitened'][monthcounter][yearcounter] * \
                            reservoir.monthly[data_type]['white_std'][monthcounter] + \
                            reservoir.monthly[data_type]['white_mean'][monthcounter]

                if plot_key == reservoir.key:
                    fig = plt.figure()
                    gs = gridspec.GridSpec(12, 2)
                    for monthcounter in range(0, 12):
                        ax1 = plt.subplot(gs[monthcounter, 0])
                        ax1.plot(reservoir.monthly_new[data_type]['flows'][monthcounter])
                        ax1.set_ylabel(self.monthlist[monthcounter])
                        ax1 = plt.subplot(gs[monthcounter, 1])
                        ax1.plot(reservoir.monthly_new[data_type]['whitened'][monthcounter])
                        ax1.set_ylabel(self.monthlist[monthcounter])
                    fig.suptitle(reservoir.key + " " + data_type)
                    plt.show()
                    plt.close()

    def add_error_delta(self, numYears, plot_key):
        for deltaname in self.delta_list:
            for monthcounter in range(0, 12):
                for yearcounter in range(0, numYears):
                    self.monthly_new[deltaname]['whitened'][monthcounter][yearcounter] += \
                    self.monthly_new[deltaname]['whitened_residuals'][monthcounter][yearcounter] * \
                    self.monthly[deltaname]['res_std'][monthcounter] + self.monthly[deltaname]['res_mean'][monthcounter]

                    if self.monthly[deltaname]['use_log'][monthcounter] == 'no':
                        if self.monthly_new[deltaname]['whitened'][monthcounter][yearcounter] > \
                                self.monthly[deltaname]['hist_max'][monthcounter]:
                            self.monthly_new[deltaname]['whitened'][monthcounter][yearcounter] = \
                            self.monthly[deltaname]['hist_max'][monthcounter]
                        elif self.monthly_new[deltaname]['whitened'][monthcounter][yearcounter] < \
                                self.monthly[deltaname]['hist_min'][monthcounter]:
                            self.monthly_new[deltaname]['whitened'][monthcounter][yearcounter] = \
                            self.monthly[deltaname]['hist_min'][monthcounter]

                    if self.monthly[deltaname]['use_log'][monthcounter] == 'yes':
                        self.monthly_new[deltaname]['gains'][monthcounter][yearcounter] = np.exp(
                            self.monthly_new[deltaname]['whitened'][monthcounter][yearcounter] *
                            self.monthly[deltaname]['white_std'][monthcounter] + self.monthly[deltaname]['white_mean'][
                                monthcounter])
                    else:
                        self.monthly_new[deltaname]['gains'][monthcounter][yearcounter] = \
                        self.monthly_new[deltaname]['whitened'][monthcounter][yearcounter] * \
                        self.monthly[deltaname]['white_std'][monthcounter] + self.monthly[deltaname]['white_mean'][
                            monthcounter]
            if plot_key == deltaname:
                fig = plt.figure()
                gs = gridspec.GridSpec(12, 2)
                for monthcounter in range(0, 12):
                    ax1 = plt.subplot(gs[monthcounter, 0])
                    ax1.plot(self.monthly_new[deltaname]['gains'][monthcounter])
                    ax1.set_ylabel(self.monthlist[monthcounter])
                    ax1 = plt.subplot(gs[monthcounter, 1])
                    ax1.plot(self.monthly_new[deltaname]['whitened'][monthcounter])
                    ax1.set_ylabel(self.monthlist[monthcounter])
                fig.suptitle(deltaname)
                plt.show()
                plt.close()

    def make_daily_timeseries(self, numYears, start_date, end_date, start_year, first_leap, plot_key, file_folder, file_name):
        dates_for_output = pd.date_range(start=start_date, end=end_date, freq='D')
        output_day_year = dates_for_output.dayofyear
        output_year = dates_for_output.year
        output_month = dates_for_output.month
        output_day_month = dates_for_output.day
        output_dowy = water_day(output_day_year, output_year)

        numdays_output = len(dates_for_output)
        last_step_month = output_month[0] - 2
        for reservoir in self.reservoir_list:
            reservoir.daily_output_data = {}
            reservoir.k_close_wateryear = {}
            for data_type in self.data_type_list:
                reservoir.daily_output_data[data_type] = np.zeros(numdays_output)
            reservoir.daily_output_data['snow'] = np.zeros(numdays_output)
        self.k_close_wateryear = {}
        self.daily_output_data = {}
        for deltaname in self.delta_list:
            self.daily_output_data[deltaname] = np.zeros(numdays_output)

        for t in range(0, numdays_output):
            monthcounter = output_month[t] - 1
            yearcounter = output_year[t] - start_year
            daycounter = output_day_month[t] - 1
            dowy = output_dowy[t]
            is_leap = (yearcounter % 4 == first_leap)
            year_leap_non_leap = np.where(is_leap, self.leap_year, self.non_leap_year)

            if monthcounter == 1 and daycounter == 28:
                daycounter = 27
            for reservoir in self.reservoir_list:
                for data_type in self.data_type_list:
                    if last_step_month != monthcounter:
                        for sorted_search in range(0, len(reservoir.monthly[data_type]['sorted'][monthcounter])):
                            if reservoir.monthly_new[data_type]['flows'][monthcounter][yearcounter] < \
                                    reservoir.monthly[data_type]['sorted'][monthcounter][sorted_search]:
                                break
                        reservoir.k_close_wateryear[data_type] = int(
                            reservoir.monthly[data_type]['sort_index'][monthcounter][sorted_search])

                    reservoir.daily_output_data[data_type][t] = (reservoir.monthly_new[data_type]['flows'][
                                                                     monthcounter][yearcounter] -
                                                                 reservoir.monthly[data_type]['baseline_value'][
                                                                     monthcounter][
                                                                     reservoir.k_close_wateryear[data_type]] *
                                                                 self.days_in_month[year_leap_non_leap][monthcounter]) * \
                                                                reservoir.monthly[data_type]['daily'][
                                                                    self.monthlist[monthcounter]][
                                                                    reservoir.k_close_wateryear[data_type]][
                                                                    daycounter] + \
                                                                reservoir.monthly[data_type]['baseline_value'][
                                                                    monthcounter][
                                                                    reservoir.k_close_wateryear[data_type]]
                if last_step_month != monthcounter:
                    this_year_fnf_melt = 0.0
                    for melt_month in range(3, 7):
                        if monthcounter < 9:
                            this_year_fnf_melt += reservoir.monthly_new['fnf']['flows'][melt_month][yearcounter]
                        else:
                            if yearcounter < (numYears - 1):
                                this_year_fnf_melt += reservoir.monthly_new['fnf']['flows'][melt_month][yearcounter + 1]
                    for sorted_search in range(0, len(reservoir.monthly['snowmelt_sorted'])):
                        if this_year_fnf_melt < reservoir.monthly['snowmelt_sorted'][sorted_search]:
                            break
                    reservoir.k_close_wateryear['snow'] = int(reservoir.monthly['snowmelt_sort_index'][sorted_search])

                reservoir.daily_output_data['snow'][t] = reservoir.snowpack['pred_max'][yearcounter] * \
                                                         reservoir.snowpack['daily'][
                                                             reservoir.k_close_wateryear['snow']][dowy]

            for deltaname in self.delta_list:
                if last_step_month != monthcounter:
                    for sorted_search in range(0, len(self.monthly[deltaname]['sorted'][monthcounter])):
                        if self.monthly_new[deltaname]['gains'][monthcounter][yearcounter] < \
                                self.monthly[deltaname]['sorted'][monthcounter][sorted_search]:
                            break
                    self.k_close_wateryear[deltaname] = int(
                        self.monthly[deltaname]['sort_index'][monthcounter][sorted_search])

                self.daily_output_data[deltaname][t] = (self.monthly_new[deltaname]['gains'][monthcounter][
                                                            yearcounter] -
                                                        self.monthly[deltaname]['baseline_value'][monthcounter][
                                                            self.k_close_wateryear[deltaname]] * self.days_in_month[year_leap_non_leap][
                                                            monthcounter]) * \
                                                       self.monthly[deltaname]['daily'][self.monthlist[monthcounter]][
                                                           self.k_close_wateryear[deltaname]][daycounter] + \
                                                       self.monthly[deltaname]['baseline_value'][monthcounter][
                                                           self.k_close_wateryear[deltaname]]

            last_step_month = monthcounter

        for start_counter in range(0, numdays_output):
            monthcounter = output_month[start_counter]
            daycounter = output_day_month[start_counter]
            if monthcounter == 10 and daycounter == 1:
                break
        for end_counter in range(numdays_output - 1, 0, -1):
            monthcounter = output_month[end_counter]
            daycounter = output_day_month[end_counter]
            if monthcounter == 9 and daycounter == 30:
                break
            # print(end_counter, end=" ")
            # print(monthcounter, end=" ")
            # print(daycounter)

        dates_for_df = dates_for_output[start_counter:(end_counter + 1)]
        df_for_output = pd.DataFrame(index=dates_for_df)
        for reservoir in self.reservoir_list:
            reservoir.daily_df_data = {}
            reservoir.daily_df_data['snow'] = reservoir.daily_output_data['snow'][start_counter:(end_counter + 1)]
            for data_type in self.data_type_list:
                reservoir.daily_df_data[data_type] = reservoir.daily_output_data[data_type][
                                                     start_counter:(end_counter + 1)]
                if data_type == 'fnf':
                    multiplier = 1000.0
                elif data_type == 'fci':
                    multiplier = 1.0
                else:
                    multiplier = 1.0 / cfs_tafd
                key_name = reservoir.key + "_" + data_type
                df_for_output['%s_%s' % (reservoir.key, data_type)] = pd.Series(
                    reservoir.daily_df_data[data_type] * multiplier, index=df_for_output.index)
            df_for_output['%s_snow' % (reservoir.key)] = pd.Series(reservoir.daily_df_data['snow'],
                                                                   index=df_for_output.index)
        self.daily_df_data = {}
        for deltaname in self.delta_list:
            self.daily_df_data[deltaname] = self.daily_output_data[deltaname][start_counter:(end_counter + 1)]
            multiplier = 1.0 / cfs_tafd
            if deltaname == 'SAC' or deltaname == 'SJ' or deltaname == 'EAST':
                df_for_output['%s_gains' % deltaname] = pd.Series(self.daily_df_data[deltaname] * multiplier,
                                                                  index=df_for_output.index)
            elif deltaname == 'depletions':
                df_for_output['delta_depletions'] = pd.Series(self.daily_df_data[deltaname] * multiplier,
                                                              index=df_for_output.index)
            else:
                df_for_output['%s_pump' % deltaname] = pd.Series(self.daily_df_data[deltaname] * multiplier,
                                                                 index=df_for_output.index)
        df_for_output.to_csv(file_folder + 'cord-data-' + file_name, index=True, index_label='datetime')

        for reservoir in self.reservoir_list:
            if plot_key == reservoir.key:
                for data_type in self.data_type_list:
                    fig = plt.figure()
                    gs = gridspec.GridSpec(2, 1)
                    if data_type == 'fnf':
                        ax1 = plt.subplot(gs[0, 0])
                        ax1.plot(reservoir.daily_output_data[data_type][0:len(reservoir.fnf)], c='red')
                        ax1.plot(range(274, 274 + len(reservoir.fnf)), reservoir.fnf * 1000.0, c='black')
                        ax2 = plt.subplot(gs[1, 0])
                        ax2.plot(reservoir.daily_output_data[data_type], c='red')
                    elif data_type == 'inf':
                        ax1 = plt.subplot(gs[0, 0])
                        ax1.plot(reservoir.daily_output_data[data_type][0:len(reservoir.fnf)], c='red')
                        ax1.plot(range(274, 274 + len(reservoir.Q)), reservoir.Q, c='black')
                        ax2 = plt.subplot(gs[1, 0])
                        ax2.plot(reservoir.daily_output_data[data_type], c='red')
                    elif data_type == 'gains':
                        ax1 = plt.subplot(gs[0, 0])
                        ax1.plot(reservoir.daily_output_data[data_type][0:len(reservoir.fnf)], c='red')
                        ax1.plot(range(274, 274 + len(reservoir.downstream)), reservoir.downstream, c='black')
                        ax2 = plt.subplot(gs[1, 0])
                        ax2.plot(reservoir.daily_output_data[data_type], c='red')
                    elif data_type == 'evap':
                        ax1 = plt.subplot(gs[0, 0])
                        ax1.plot(reservoir.daily_output_data[data_type][0:len(reservoir.fnf)], c='red')
                        ax1.plot(range(274, 274 + len(reservoir.E)), reservoir.E, c='black')
                        ax2 = plt.subplot(gs[1, 0])
                        ax2.plot(reservoir.daily_output_data[data_type], c='red')
                    elif data_type == 'precip':
                        ax1 = plt.subplot(gs[0, 0])
                        ax1.plot(reservoir.daily_output_data[data_type][0:len(reservoir.fnf)], c='red')
                        ax1.plot(range(274, 274 + len(reservoir.precip)), reservoir.precip, c='black')
                        ax2 = plt.subplot(gs[1, 0])
                        ax2.plot(reservoir.daily_output_data[data_type], c='red')
                    elif data_type == 'fci':
                        ax1 = plt.subplot(gs[0, 0])
                        ax1.plot(reservoir.daily_output_data[data_type][0:len(reservoir.fnf)], c='red')
                        ax1.plot(range(274, 274 + len(reservoir.fci)), reservoir.fci, c='black')
                        ax2 = plt.subplot(gs[1, 0])
                        ax2.plot(reservoir.daily_output_data[data_type], c='red')
                    fig.suptitle(reservoir.key + " " + data_type)
                    plt.show()
                    plt.close()

                fig = plt.figure()
                gs = gridspec.GridSpec(2, 1)
                ax1 = plt.subplot(gs[0, 0])
                ax1.plot(reservoir.daily_output_data['snow'][0:len(reservoir.fnf)], c='red')
                ax1.plot(range(274, 274 + len(reservoir.SNPK)), reservoir.SNPK, c='black')
                ax2 = plt.subplot(gs[1, 0])
                ax2.plot(reservoir.daily_output_data['snow'], c='red')
                fig.suptitle(reservoir.key + " snow")
                plt.show()
                plt.close()

        for deltaname in self.delta_list:
            if plot_key == deltaname:
                fig = plt.figure()
                gs = gridspec.GridSpec(2, 1)
                ax1 = plt.subplot(gs[0, 0])
                ax1.plot(self.daily_output_data[deltaname], c='red')
                ax2 = plt.subplot(gs[1, 0])
                ax2.plot(self.daily_output_data[deltaname][0:len(self.df.SAC_gains)], c='red')
                if deltaname == 'SAC':
                    ax2.plot(range(274, 274 + len(self.df.SAC_gains)), self.df.SAC_gains * cfs_tafd, c='black')
                elif deltaname == 'SJ':
                    ax2.plot(range(274, 274 + len(self.df.SJ_gains)), self.df.SJ_gains * cfs_tafd, c='black')
                elif deltaname == 'EAST':
                    ax2.plot(range(274, 274 + len(self.df.EAST_gains)), self.df.EAST_gains * cfs_tafd, c='black')
                elif deltaname == 'depletions':
                    ax2.plot(range(274, 274 + len(self.df.delta_depletions)), self.df.delta_depletions * cfs_tafd,
                             c='black')
                elif deltaname == 'CCC':
                    ax2.plot(range(274, 274 + len(self.df.CCC_pump)), self.df.CCC_pump * cfs_tafd, c='black')
                elif deltaname == 'BRK':
                    ax2.plot(range(274, 274 + len(self.df.BRK_pump)), self.df.BRK_pump * cfs_tafd, c='black')
                fig.suptitle(deltaname)
                plt.show()
                plt.close()

    def get_flow_ratios(self, inf, fnf):
        ratios = np.zeros(self.number_years)
        for year_counter in range(0, self.number_years):
            if inf[year_counter] > 0 and fnf[year_counter] > 0:
                ratios[year_counter] = inf[year_counter] - fnf[year_counter]
            else:
                ratios[year_counter] = 0.0

        return ratios

    def make_regression(self, independent, dependent, use_zeros):

        if sum(independent) == 0.0:
            coef = np.zeros(2)
            coef[0] = 0.0
            coef[1] = np.mean(dependent)
        else:
            if use_zeros == 'no':
                coef = np.polyfit(independent[(independent > 0) & (dependent > 0)],
                                  dependent[(independent > 0) & (dependent > 0)], 1)
            else:
                coef = np.polyfit(independent, dependent, 1)

        predicted_deviation = np.zeros(len(independent))
        for y in range(0, len(independent)):
            predicted_deviation[y] = dependent[y] - coef[0] * independent[y] - coef[1]

        return coef, predicted_deviation

    def whiten_data(self, data):
        residuals = np.zeros(len(data))
        ssq = 0.0
        for x in range(0, len(data)):
            ssq += np.power(data[x], 2)
        if ssq > 0.0:
            data_mean = np.mean(data)
            data_std = np.std(data)
        else:
            data_mean = 0.0
            data_std = 1.0
        if data_std > 0.0:
            for x in range(0, len(data)):
                residuals[x] = (data[x] - data_mean) / data_std
        else:
            for x in range(0, len(data)):
                residuals[x] = (data[x] - data_mean)

        return residuals, data_mean, data_std

    def unfold_series(self, annual_cycle, start_cycle):
        array_shape = np.shape(annual_cycle)
        series_length = array_shape[0] * array_shape[1]
        new_series = np.zeros((series_length, 1))
        for y in range(0, array_shape[1]):
            for x in range(0, array_shape[0]):
                cycle_value = x + start_cycle - 1
                if cycle_value >= array_shape[0]:
                    cycle_value -= array_shape[0]
                new_series[x + y * array_shape[0]] = annual_cycle[cycle_value][y]

        return new_series

    def backcast_ar(self, residuals, lagged_residuals):
        timestep = len(residuals)
        predictors = residuals[0:(timestep - lag)]
        for x in range(1, lag):
            start_value = x
            end_value = timestep - (lag - x)

            predictors = np.hstack((predictors, residuals[start_value:end_value]))
        predictors = np.hstack((predictors, np.ones((timestep - lag, 1))))
        values = np.linalg.lstsq(predictors, residuals[lag:timestep])
        # print(values)

        return values

