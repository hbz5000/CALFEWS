##################################################################################
#
# Combined Tulare Basin / SF Delta Model
# Still in development - not ready for publication
#
# This model is designed to simulate surface water flows throughout the CA Central Valley, including:
# (a) Major SWP/CVP Storage in the Sacramento River Basin
# (b) San Joaquin River controls at New Melones, Don Pedro, and Exchequer Reservoirs
# (c) Delta environmental controls, as outlined in D1641 Bay Delta Standards & NMFS Biological Opinions for the Bay-Delta System
# (d) Cordination between Delta Pumping and San Luis Reservoir
# (e) Local sources of water in Tulare Basin (8/1/18 - includes Millerton, Kaweah, Success, and Isabella Reservoirs - only Millerton & Isabella are currently albrated)
# (f) Conveyence and distribution capacities in the Kern County Canal System, including CA Aqueduct, Friant-Kern Canal, Kern River Channel system, and Cross Valley Canal
# (g) Agricultural demands & groundwater recharge/recovery capacities
# (h) Pumping off the CA Aqueduct to Urban demands in the South Bay, Central Coast, and Southern California
##################################################################################
import numpy as np
from scipy.optimize import curve_fit, differential_evolution
import warnings
from sklearn import linear_model
from sklearn.decomposition import PCA

from cord import *

eps = 1e-13

# model_mode = 'simulation'
model_mode = 'validation'
# model_mode = 'forecast'

demand_type = 'pesticide'
# demand_type = 'pmp'
# demand_type = 'old'

# To run full dataset, short_test = -1. Else enter number of days to run, startoutg at sd. e.g. 365 for 1 year only.
short_test = -1

### simulation scenarios for testing (see model.set_regulations_current_south)
# scenarios = []
#
# scenario1 = {}
# scenario1['results_folder'] = 'cord/data/results/FKC_capacity_wy2017'
# scenario1['FKC'] = 'cord/scenarios/FKC_properties__capacity_wy2017.json'
# scenario1['LWT'] = 'baseline'
# scenarios.append(scenario1)

# for i in [0]:
#   main_functions.run_formulation(scenarios[i], model_mode, demand_type, short_test)

### get model data from sensitivity analysis
nscenarios = 30
nyears = 20
Xin =  []
Xout =  []
params = pd.read_csv('cord/data/results/sensitivity_params.csv').iloc[:,5:]
nparams = params.shape[1]
Xparam = []

for x in range(nscenarios):
  modelno = pd.read_pickle('cord/data/results/modelno' + str(x) + '.pkl')
  modelso = pd.read_pickle('cord/data/results/modelso' + str(x) + '.pkl')

  ### get model inputs
  index = 0
  for i in range(nyears):
    Xparam = np.append(Xparam, params.iloc[x, :])
    for j in range(len(modelno.reservoir_list)):
      if hasattr(modelno.reservoir_list[j], 'fnf'):
        Xin = np.append(Xin, modelno.reservoir_list[j].fnf[index:(index+365)].cumsum())
    for j in range(len(modelso.reservoir_list)):
      if hasattr(modelso.reservoir_list[j], 'fnf'):
        Xin = np.append(Xin, modelso.reservoir_list[j].fnf[index:(index+365)].cumsum())
    index += 365
    if (modelso.dowy[index] == 364):
      index += 1

  # same for model output
  index = 0
  for i in range(nyears):
    # Xout = np.append(Xout, modelno.delta.HRO_pump[index:(index + 365)].cumsum())
    # Xout = np.append(Xout, modelno.delta.TRP_pump[index:(index + 365)].cumsum())
    Xout = np.append(Xout, modelso.semitropic.daily_supplies_full['tableA_delivery'][index:(index + 365)])
    Xout = np.append(Xout, modelso.semitropic.daily_supplies_full['tableA_flood'][index:(index + 365)])
    Xout = np.append(Xout, modelso.semitropic.daily_supplies_full['friant1_flood'][index:(index + 365)])
    Xout = np.append(Xout, modelso.semitropic.daily_supplies_full['kings_flood'][index:(index + 365)])
    index += 365
    if (modelso.dowy[index] == 364):
      index += 1

### now do the pca for input features
nfeatures = int(len(Xin) / (nscenarios * nyears * 365))
Xin = Xin.reshape(nyears * nscenarios, 365 * nfeatures)
Xparam = Xparam.reshape(nyears * nscenarios, nparams)
norm = np.zeros(nfeatures)
Xin_norm = np.zeros(Xin.shape)
for i in range(nfeatures):
  norm[i] = np.max(Xin[:, (i * 365) + 364])
  Xin_norm[:, (i * 365):((i + 1) * 365)] = Xin[:, (i * 365):((i + 1) * 365)] / norm[i]
mean_signal = Xin_norm.mean(axis=0)
Xin_norm -= mean_signal

# reduce dimension & smooth with pca
pca_in = PCA(0.99)
pca_in.fit(Xin_norm)
pca_in.explained_variance_ratio_.cumsum()
Xin_norm_transform = pca_in.transform(Xin_norm)
Xin_norm_hat = pca_in.inverse_transform(Xin_norm_transform)
Xin_hat = (Xin_norm_hat + mean_signal)
for i in range(nfeatures):
  Xin_hat[:, (i*365):((i+1)*365)] *= norm[i]

# plot
fig = plt.figure()
ax = plt.subplot(3,3,1)
for i in range(nyears * nscenarios):
  ax.plot(Xin[i])
ax = plt.subplot(3,3,2)
for i in range(nyears * nscenarios):
  ax.plot(Xin_norm[i])
ax = plt.subplot(3,3,3)
for i in range(nyears * nscenarios):
  ax.plot(Xin_norm_transform[i])
ax = plt.subplot(3,3,4)
for i in range(nyears * nscenarios):
  ax.plot(Xin_hat[i])
ax = plt.subplot(3,3,5)
for i in range(nyears * nscenarios):
  ax.plot(Xin_norm_hat[i])
ax = plt.subplot(3, 3, 6)
for i in range(pca_in.n_components_):
  ax.plot(pca_in.components_[i])
ax = plt.subplot(3,3,7)
for i in range(nyears * nscenarios):
  ax.plot(Xin[i] - Xin_hat[i])
ax = plt.subplot(3,3,8)
for i in range(nyears * nscenarios):
  ax.plot(Xin_norm[i] - Xin_norm_hat[i])

# plt.scatter(Xin_norm_transform[:,0], Xin_norm_transform[:,1])




### same for output features
nfeatures = int(len(Xout) / (nscenarios * nyears * 365))
Xout = Xout.reshape(nyears * nscenarios, 365 * nfeatures)
norm = np.zeros(nfeatures)
Xout_norm = np.zeros(Xout.shape)
for i in range(nfeatures):
  norm[i] = np.max(Xout[:, (i*365)+364])
  Xout_norm[:, (i*365):((i+1)*365)] = Xout[:, (i*365):((i+1)*365)] / norm[i]
mean_signal = Xout_norm.mean(axis=0)
Xout_norm -= mean_signal

# reduce dimension & smooth with pca
pca_out = PCA(0.99)
pca_out.fit(Xout_norm)
pca_out.explained_variance_ratio_.cumsum()
Xout_norm_transform = pca_out.transform(Xout_norm)
Xout_norm_hat = pca_out.inverse_transform(Xout_norm_transform)
Xout_hat = (Xout_norm_hat + mean_signal)
for i in range(nfeatures):
  Xout_hat[:, (i*365):((i+1)*365)] *= norm[i]

# plot
fig = plt.figure()
ax = plt.subplot(3,3,1)
for i in range(nyears * nscenarios):
  ax.plot(Xout[i])
ax = plt.subplot(3,3,2)
for i in range(nyears * nscenarios):
  ax.plot(Xout_norm[i])
ax = plt.subplot(3,3,3)
for i in range(nyears * nscenarios):
  ax.plot(Xout_norm_transform[i])
ax = plt.subplot(3,3,4)
for i in range(nyears * nscenarios):
  ax.plot(Xout_hat[i])
ax = plt.subplot(3,3,5)
for i in range(nyears * nscenarios):
  ax.plot(Xout_norm_hat[i])
ax = plt.subplot(3,3,6)
for i in range(pca_out.n_components_):
  ax.plot(pca_out.components_[i])
ax = plt.subplot(3,3,7)
for i in range(nyears * nscenarios):
  ax.plot(Xout[i] - Xout_hat[i])
ax = plt.subplot(3,3,8)
for i in range(nyears * nscenarios):
  ax.plot(Xout_norm[i] - Xout_norm_hat[i])

# plt.scatter(Xout_norm_transform[:,0], Xout_norm_transform[:,1])


# ### compare input PCs to output (PCs+sensitivityFactors)
# Xcombined = pd.DataFrame(np.hstack((Xin_norm_transform, Xparam, Xout_norm_transform)))
# sns.pairplot(Xcombined)
# corrs = np.zeros([pca_in.n_components_, pca_out.n_components_])
# for i in range(pca_in.n_components_):
#   for j in range(pca_out.n_components_):
#     corrs[i,j] = np.corrcoef(Xin_norm_transform[:,i], Xout_norm_transform[:,j])[0,1]

### linear model mapping input PCs to output PCs
# Create linear regression object
regr = linear_model.LinearRegression()

# Train the model using the training sets
regr.fit(np.hstack((Xin_norm_transform, Xparam)), Xout_norm_transform)
print('Coefficients: \n', regr.coef_)
print('R^2: \n', regr.score(np.hstack((Xin_norm_transform, Xparam)), Xout_norm_transform))

# Make predictions using the testing set
Xout_norm_transform_predict = regr.predict(np.hstack((Xin_norm_transform, Xparam)))
Xout_norm_predict = pca_out.inverse_transform(Xout_norm_transform_predict)
Xout_predict = (Xout_norm_predict + mean_signal)
for i in range(nfeatures):
  Xout_predict[:, (i*365):((i+1)*365)] *= norm[i]

# plot predictions vs actual
col = ['r','orange','y','g','b','c']
for i in range(6):
  plt.plot(Xout[i], c=col[i])
  # plt.plot(Xout_hat[i], c=col[i], ls=':')
  plt.plot(Xout_predict[i], c=col[i], ls='--')

fig = plt.figure()
for i in range(3):
  for j in range(2):
    ax = plt.subplot(2,3,(2*i+j+1))
    plt.scatter(Xout_norm_transform[:,(2*i+j)], Xout_norm_transform_predict[:,(2*i+j)], alpha=0.4)
    axmin = max(Xout_norm_transform[:,(2*i+j)].min(), Xout_norm_transform_predict[:,(2*i+j)].min())
    axmax = min(Xout_norm_transform[:,(2*i+j)].max(), Xout_norm_transform_predict[:,(2*i+j)].max())
    plt.plot([axmin,axmax],[axmin,axmax],c='k')





#############################################
### Try instead with fitted sigmoid functions
#############################################



def sumSigmoid1(t, c, L1, k1, tau1):
  return np.maximum(c + L1 / (1.0 + numpy.exp(-k1 * (t - tau1))), np.zeros(len(t)))

def sumSigmoid2(t, c, L1, k1, tau1, L2=0, k2=0, tau2=0):
  return np.maximum(c + L1 / (1.0 + numpy.exp(-k1 * (t - tau1))) + L2 / (1.0 + numpy.exp(-k2 * (t - tau2))), np.zeros(len(t)))

def sumSigmoid3(t, c, L1, k1, tau1, L2=0, k2=0, tau2=0, L3=0, k3=0, tau3=0):
  return np.maximum(c + L1 / (1.0 + numpy.exp(-k1 * (t - tau1))) + L2 / (1.0 + numpy.exp(-k2 * (t - tau2))) + L3 / (1.0 + numpy.exp(-k3 * (t - tau3))), np.zeros(len(t)))

def sumOfSquaredError1(parameterTuple):
    warnings.filterwarnings("ignore") # do not print warnings by genetic algorithm
    val = sumSigmoid1(tData, *parameterTuple)
    return numpy.sum((xData - val) ** 2.0)

def sumOfSquaredError2(parameterTuple):
  warnings.filterwarnings("ignore")  # do not print warnings by genetic algorithm
  val = sumSigmoid2(tData, *parameterTuple)
  return numpy.sum((xData - val) ** 2.0)

def sumOfSquaredError3(parameterTuple):
  warnings.filterwarnings("ignore")  # do not print warnings by genetic algorithm
  val = sumSigmoid3(tData, *parameterTuple)
  return numpy.sum((xData - val) ** 2.0)

# fit model as sum of constant plus 1-3 sigmoid functions. if numSigmoid>1, fit iteratively.
def fitSigmoid(numSigmoid, tData, xData):
  # min and max used for bounds
  maxT = max(tData)
  maxX = max(xData)

  if (maxX < eps):
    fittedParameters = [0,0,0,0]
    if (numSigmoid > 1):
      fittedParameters = np.append(fittedParameters, [0,0,0])
      if (numSigmoid > 2):
        fittedParameters = np.append(fittedParameters, [0, 0, 0])
    return fittedParameters, 0
  else:
    parameterMin = []
    parameterMax = []
    parameterMax.append(maxX) # seach bounds for Offset
    parameterMax.append(2*maxX) # seach bounds for L1
    parameterMax.append(maxT) # seach bounds for k1
    parameterMax.append(2*maxT) # seach bounds for tau1
    parameterMax.append(2*maxX) # seach bounds for L1
    parameterMax.append(maxT) # seach bounds for k1
    parameterMax.append(2*maxT) # seach bounds for tau1
    parameterMax.append(2*maxX) # seach bounds for L1
    parameterMax.append(maxT) # seach bounds for k1
    parameterMax.append(2*maxT) # seach bounds for tau1
    parameterMin.append(-maxX) # seach bounds for Offset
    parameterMin.append(0.0) # seach bounds for L1
    parameterMin.append(0.0) # seach bounds for k1
    parameterMin.append(-maxT) # seach bounds for tau1
    parameterMin.append(0.0) # seach bounds for L1
    parameterMin.append(0.0) # seach bounds for k1
    parameterMin.append(-maxT) # seach bounds for tau1
    parameterMin.append(0.0) # seach bounds for L1
    parameterMin.append(0.0) # seach bounds for k1
    parameterMin.append(-maxT) # seach bounds for tau1

    try:
      p0 = [0., maxX, 6/maxT, maxT/2]
      fittedParameters, pcov = curve_fit(sumSigmoid1, tData, xData, p0, bounds=(parameterMin[:4], parameterMax[:4]))
    except:
      p0[2] = 100
      p0[3] = np.argwhere(xData==xData.max())[0][0]
      fittedParameters, pcov = curve_fit(sumSigmoid1, tData, xData, p0, bounds=(parameterMin[:4], parameterMax[:4]))

    if (numSigmoid == 1):
      return fittedParameters, pcov
    else:
      p02 = np.append(fittedParameters, p0[1:4])
      p02[1] *= 0.8
      p02[4] *= 0.2
      try:
        fittedParameters, pcov = curve_fit(sumSigmoid2, tData, xData, p02, bounds=(parameterMin[:7], parameterMax[:7]))
      except:
        fittedParameters = np.append(fittedParameters, [0., 0., 0.])
      if (numSigmoid == 2):
        return fittedParameters, pcov
      else:
        p03 = np.append(fittedParameters, p0[1:4])
        p03[1] *= 0.8
        p03[4] *= 0.8
        p03[7] *= 0.2
        fittedParameters, pcov = curve_fit(sumSigmoid3, tData, xData, p03, bounds=(parameterMin, parameterMax))
        return fittedParameters, pcov




### run sigmoid regression for input and input variables
nsigmoid = 1
nparam = 1 + 3 * nsigmoid
nfeatures_in = int(Xin.shape[1] / 365)
Pin_sigmoid = np.zeros([Xin.shape[0], nfeatures_in * nparam])
Xin_fit = np.zeros(Xin.shape)
for i in range(Xin.shape[0]):
  for j in range(nfeatures_in):
    fittedParameters, pcov = fitSigmoid(nsigmoid, np.arange(365), Xin[i, (j*365):((j+1)*365)])
    if (nsigmoid > 1):
      if (fittedParameters[1] < fittedParameters[4]):
        dum = fittedParameters[1:4].copy()
        fittedParameters[1:4] = fittedParameters[4:]
        fittedParameters[4:] = dum
    Pin_sigmoid[i, (j*nparam):((j+1)*nparam)] = fittedParameters
    Xin_fit[i, (j*365):((j+1)*365)] = sumSigmoid2(np.arange(365), *fittedParameters)
nfeatures_out = int(Xout.shape[1] / 365)
Pout_sigmoid = np.zeros([Xout.shape[0], nfeatures_out * nparam])
Xout_fit = np.zeros(Xout.shape)
for i in range(Xout.shape[0]):
  for j in range(nfeatures_out):
    fittedParameters, pcov = fitSigmoid(nsigmoid, np.arange(365), Xout[i, (j*365):((j+1)*365)])
    if (nsigmoid > 1):
      if (fittedParameters[1] < fittedParameters[4]):
        dum = fittedParameters[1:4].copy()
        fittedParameters[1:4] = fittedParameters[4:]
        fittedParameters[4:] = dum
    Pout_sigmoid[i, (j*nparam):((j+1)*nparam)] = fittedParameters
    Xout_fit[i, (j*365):((j+1)*365)] = sumSigmoid2(np.arange(365), *fittedParameters)





### plot fitted curves & params
fig = plt.figure()
plt.subplot(2,2,1)
for i in range(5):
  xData=Xin[i]
  xFit=Xin_fit[i]
  tData = np.arange(Xin.shape[1])
  plt.plot(tData, xData, 'k')
  plt.plot(tData, xFit, 'b', ls='--')
plt.subplot(2,2,2)
for i in range(5):
  xData=Xout[i]
  xFit=Xout_fit[i]
  tData = np.arange(Xout.shape[1])
  plt.plot(tData, xData, 'k')
  plt.plot(tData, xFit, 'b', ls='--')
plt.subplot(2,2,3)
for i in range(5):
  pFit=Pin_sigmoid_norm[i]
  tData = np.arange(len(pFit))
  plt.plot(tData, pFit, 'b', ls='--')
plt.subplot(2,2,4)
for i in range(5):
  pFit=Pout_sigmoid_norm[i]
  tData = np.arange(len(pFit))
  plt.plot(tData, pFit, 'b', ls='--')


### Now PCA for input & output params
# first standardize
Pin_sigmout_mean = Pin_sigmoid.mean(axis=0)
Pin_sigmout_std = Pin_sigmoid.std(axis=0)
Pin_sigmoid_norm = (Pin_sigmoid - Pin_sigmout_mean) / Pin_sigmout_std
Pout_sigmout_mean = Pout_sigmoid.mean(axis=0)
Pout_sigmout_std = Pout_sigmoid.std(axis=0)
Pout_sigmoid_norm = (Pout_sigmoid - Pout_sigmout_mean) / Pout_sigmout_std
# now run pca
pca_in = PCA(0.99)
pca_in.fit(Pin_sigmoid_norm)
pca_in.explained_variance_ratio_.cumsum()
pca_out = PCA(0.99)
pca_out.fit(Pout_sigmoid_norm)
pca_out.explained_variance_ratio_.cumsum()
# inverse transform to get smoothed sigmoid params
Pin_sigmoid_norm_transform = pca_in.transform(Pin_sigmoid_norm)
Pin_sigmoid_norm_hat = pca_in.inverse_transform(Pin_sigmoid_norm_transform)
Pin_sigmoid_hat = Pin_sigmoid_norm_hat * Pin_sigmout_std + Pin_sigmout_mean
Pout_sigmoid_norm_transform = pca_out.transform(Pout_sigmoid_norm)
Pout_sigmoid_norm_hat = pca_out.inverse_transform(Pout_sigmoid_norm_transform)
Pout_sigmoid_hat = Pout_sigmoid_norm_hat * Pout_sigmout_std + Pout_sigmout_mean
# now get smoothed curves in real space
Xin_fit_hat = np.zeros(Xin.shape)
for i in range(Xin.shape[0]):
  for j in range(nfeatures_in):
    Xin_fit_hat[i, (j*365):((j+1)*365)] = sumSigmoid2(np.arange(365), *Pin_sigmoid_hat[i, (j*nparam):((j+1)*nparam)])
Xout_fit_hat = np.zeros(Xout.shape)
for i in range(Xout.shape[0]):
  for j in range(nfeatures_out):
    Xout_fit_hat[i, (j*365):((j+1)*365)] = sumSigmoid2(np.arange(365), *Pout_sigmoid_hat[i, (j*nparam):((j+1)*nparam)])


# plot fit
# plot
fig = plt.figure()
ax = plt.subplot(3,3,1)
col = ['r','orange','y','g','b','c']
for i in range(6):
  ax.plot(Xin[i], c=col[i])
  ax.plot(Xin_fit[i], c=col[i], ls=':')
ax = plt.subplot(3,3,2)
for i in range(5):
  ax.plot(Pin_sigmoid_norm[i], c=col[i])
ax = plt.subplot(3,3,3)
for i in range(5):
  ax.plot(Pin_sigmoid_norm_transform[i], c=col[i])
ax = plt.subplot(3,3,4)
for i in range(5):
  ax.plot(Xin[i], c=col[i])
  ax.plot(Xin_fit_hat[i], c=col[i], ls=':')
ax = plt.subplot(3,3,5)
for i in range(5):
  ax.plot(Pin_sigmoid_norm_hat[i], c=col[i])
ax = plt.subplot(3,3,6)
for i in range(pca_in.n_components_):
  ax.plot(pca_in.components_[i])
ax = plt.subplot(3,3,7)
for i in range(5):
  ax.plot(Xin_fit[i] - Xin_fit_hat[i], c=col[i])
ax = plt.subplot(3,3,8)
for i in range(5):
  ax.plot(Pin_sigmoid_norm[i] - Pin_sigmoid_norm_hat[i], c=col[i])


# plot fit
# plot
fig = plt.figure()
ax = plt.subplot(1,1,1)
col = ['r','orange','y','g','b','c']
for i in range(6):
  ax.plot(Xout[i], c=col[i])
  ax.plot(Xout_fit[i], c=col[i], ls=':')
ax = plt.subplot(3,3,2)
for i in range(5):
  ax.plot(Pout_sigmoid_norm[i], c=col[i])
ax = plt.subplot(3,3,3)
for i in range(5):
  ax.plot(Pout_sigmoid_norm_transform[i], c=col[i])
ax = plt.subplot(3,3,4)
for i in range(5):
  ax.plot(Xout[i], c=col[i])
  ax.plot(Xout_fit_hat[i], c=col[i], ls=':')
ax = plt.subplot(3,3,5)
for i in range(5):
  ax.plot(Pout_sigmoid_norm_hat[i], c=col[i])
ax = plt.subplot(3,3,6)
for i in range(pca_out.n_components_):
  ax.plot(pca_out.components_[i])
ax = plt.subplot(3,3,7)
for i in range(5):
  ax.plot(Xout_fit[i] - Xout_fit_hat[i], c=col[i])
ax = plt.subplot(3,3,8)
for i in range(5):
  ax.plot(Pout_sigmoid_norm[i] - Pout_sigmoid_norm_hat[i], c=col[i])




### linear model mapping input PCs to output PCs
regr = linear_model.LinearRegression()
regr.fit(np.hstack((Pin_sigmoid_norm_transform, Xparam)), Pout_sigmoid_norm_transform)
print('Coefficients: \n', regr.coef_)
print('R^2: \n', regr.score(np.hstack((Pin_sigmoid_norm_transform, Xparam)), Pout_sigmoid_norm_transform))

# Make predictions using the testing set
Pout_sigmoid_norm_transform_predict = regr.predict(np.hstack((Pin_sigmoid_norm_transform, Xparam)))
Pout_sigmoid_norm_predict = pca_out.inverse_transform(Pout_sigmoid_norm_transform_predict)
Pout_sigmoid_predict = Pout_sigmoid_norm_predict * Pout_sigmout_std + Pout_sigmout_mean
Xout_predict = np.zeros(Xout.shape)
for i in range(Xout.shape[0]):
  for j in range(nfeatures_out):
    Xout_predict[i, (j*365):((j+1)*365)] = sumSigmoid2(np.arange(365), *Pout_sigmoid_predict[i, (j*nparam):((j+1)*nparam)])


# plot predictions vs actual
col = ['r','orange','y','g','b','c']
for i in range(6):
  plt.plot(Xout[i], c=col[i])
  # plt.plot(Xout_fit[i], c=col[i], ls=':')
  # plt.plot(Xout_hat[i], c=col[i], ls=':')
  plt.plot(Xout_predict[i], c=col[i], ls='--')

fig = plt.figure()
for i in range(3):
  for j in range(2):
    ax = plt.subplot(2,3,(2*i+j+1))
    plt.scatter(Pout_sigmoid_norm_transform[:,(2*i+j)], Pout_sigmoid_norm_transform_predict[:,(2*i+j)], alpha=0.4)
    axmin = max(Pout_sigmoid_norm_transform[:,(2*i+j)].min(), Pout_sigmoid_norm_transform_predict[:,(2*i+j)].min())
    axmax = min(Pout_sigmoid_norm_transform[:,(2*i+j)].max(), Pout_sigmoid_norm_transform_predict[:,(2*i+j)].max())
    plt.plot([axmin,axmax],[axmin,axmax],c='k')





### linear model mapping input sigmoid params to output sigmoid params (no PC)
regr = linear_model.LinearRegression()
Pin_sigmoid_logk = Pin_sigmoid.copy()
Pin_sigmoid_logk[:,1::4] = np.log(Pin_sigmoid_logk[:,1::4]+0.0001)
Pin_sigmoid_logk[:,2::4] = np.log(Pin_sigmoid_logk[:,2::4]+0.0001)
Pout_sigmoid_logk = Pout_sigmoid.copy()
Pout_sigmoid_logk[:, 1::4] = np.log(Pout_sigmoid_logk[:, 1::4]+0.0001)
Pout_sigmoid_logk[:, 2::4] = np.log(Pout_sigmoid_logk[:, 2::4]+0.0001)
regr.fit(np.hstack((Pin_sigmoid_logk, Xparam)), Pout_sigmoid_logk)
print('Coefficients: \n', regr.coef_)
print('R^2: \n', regr.score(np.hstack((Pin_sigmoid_logk, Xparam)), Pout_sigmoid_logk))

# Make predictions using the testing set
Pout_sigmoid_logk_predict = regr.predict(np.hstack((Pin_sigmoid_logk, Xparam)))
Pout_sigmoid_predict = Pout_sigmoid_logk_predict.copy()
Pout_sigmoid_predict[:, 1::4] = np.exp(Pout_sigmoid_predict[:, 1::4])-0.0001
Pout_sigmoid_predict[:, 2::4] = np.exp(Pout_sigmoid_predict[:, 2::4])-0.0001
Xout_predict = np.zeros(Xout.shape)
for i in range(Xout.shape[0]):
  for j in range(nfeatures_out):
    Xout_predict[i, (j*365):((j+1)*365)] = sumSigmoid2(np.arange(365), *Pout_sigmoid_predict[i, (j*nparam):((j+1)*nparam)])


# plot predictions vs actual
col = ['r','orange','y','g','b','c']
for i in range(6):
  plt.plot(Xout[i], c=col[i])
  # plt.plot(Xout_fit[i], c=col[i], ls=':')
  # plt.plot(Xout_hat[i], c=col[i], ls=':')
  plt.plot(Xout_predict[i], c=col[i], ls='--')

fig = plt.figure()
for i in range(4):
  for j in range(3):
    ax = plt.subplot(3,4,(3*i+j+1))
    plt.scatter(Pout_sigmoid_logk[:,(3*i+j)], Pout_sigmoid_logk_predict[:,(3*i+j)], alpha=0.4)
    axmin = max(Pout_sigmoid_logk[:,(3*i+j)].min(), Pout_sigmoid_logk_predict[:,(3*i+j)].min())
    axmax = min(Pout_sigmoid_logk[:,(3*i+j)].max(), Pout_sigmoid_logk_predict[:,(3*i+j)].max())
    plt.plot([axmin,axmax],[axmin,axmax],c='k')









############ nested sigmoid model

def sigmoidNested(t, c, L_outer, k_outer, tau_outer, k_inner, tau_inner):
  return np.maximum(c + L_outer / (1.0 + np.exp(-k_outer * ((365.0 / (1.0 + np.exp(-k_inner * (t - tau_inner)))) - tau_outer))), np.zeros(len(t)))

def sumOfSquaredErrorNested(parameterTuple):
  # warnings.filterwarnings("ignore")  # do not print warnings by genetic algorithm
  val = sigmoidNested(tData, *parameterTuple)
  return np.sum((xData - val) ** 2.0)


# fit model as sum of constant plus nested sigmoid function. Inner sigmoid warps the domain.
def fitSigmoidNested(tData, xData):
  tMax = max(tData)
  xMax = max(xData)
  countFail = 0

  if (xMax < eps):
    fittedParameters = [0,0,0,0,0,0]
    return fittedParameters, 0
  else:
    parameterBounds = []
    parameterBounds.append((-2*xMax, 0)) # seach bounds for Offset
    parameterBounds.append((0, 3*xMax)) # seach bounds for L_outer
    parameterBounds.append((0,10)) # seach bounds for k_outer
    parameterBounds.append((-tMax, 2*tMax)) # seach bounds for tau_outer
    parameterBounds.append((0,0.5)) # seach bounds for k_inner
    parameterBounds.append((-tMax, 2*tMax)) # seach bounds for tau_inner

    try:
      p0 = [0., xMax, 0.01, 180, 0.01, 120]
      fittedParameters, pcov = curve_fit(sigmoidNested, tData, xData, p0,
                                         bounds=(np.array(parameterBounds)[:, 0], np.array(parameterBounds)[:, 1]))
    except:
      try:
        # get initial search vector using differential evolution
        p0 = differential_evolution(sumOfSquaredErrorNested, parameterBounds, seed=3, maxiter=10000, tol=0.00001).x

        fittedParameters, pcov = curve_fit(sigmoidNested, tData, xData, p0,
                                           bounds=(np.array(parameterBounds)[:,0], np.array(parameterBounds)[:,1]))
      except:
        fittedParameters, pcov = [0, 0, 0, 0, 0, 0], 0
    return fittedParameters, pcov

### run sigmoid regression for input and input variables
nparam = 6
nfeatures_in = int(Xin.shape[1] / 365)
Pin_nest = np.zeros([Xin.shape[0], nfeatures_in * nparam])
Xin_fit = np.zeros(Xin.shape)
for i in range(Xin.shape[0]):
  for j in range(nfeatures_in):
    print('in', i, j)
    tData = np.arange(365)
    xData = Xin[i, (j * 365):((j + 1) * 365)]
    fittedParameters, pcov = fitSigmoidNested(tData, xData)
    Pin_nest[i, (j * nparam):((j + 1) * nparam)] = fittedParameters
    Xin_fit[i, (j * 365):((j + 1) * 365)] = sigmoidNested(np.arange(365), *fittedParameters)
nfeatures_out = int(Xout.shape[1] / 365)
Pout_nest = np.zeros([Xout.shape[0], nfeatures_out * nparam])
Xout_fit = np.zeros(Xout.shape)
for i in range(Xout.shape[0]):
  for j in range(nfeatures_out):
    print('in', i, j)
    tData = np.arange(365)
    xData = Xout[i, (j * 365):((j + 1) * 365)]
    fittedParameters, pcov = fitSigmoidNested(tData, xData)
    Pout_nest[i, (j * nparam):((j + 1) * nparam)] = fittedParameters
    Xout_fit[i, (j * 365):((j + 1) * 365)] = sigmoidNested(np.arange(365), *fittedParameters)




### plot fitted curves & params
fig = plt.figure()
plt.subplot(2,1,1)
for i in range(5):
  xData=Xin[i]
  xFit=Xin_fit[i]
  tData = np.arange(Xin.shape[1])
  plt.plot(tData, xData, 'k')
  plt.plot(tData, xFit, 'b', ls='--')
plt.subplot(2,1,2)
for i in range(1):
  xData=Xout[i]
  xFit=Xout_fit[i]
  tData = np.arange(Xout.shape[1])
  plt.plot(tData, xData, 'k')
  plt.plot(tData, xFit, 'b', ls='--')
plt.subplot(2,2,3)
for i in range(5):
  pFit=Pin_sigmoid_norm[i]
  tData = np.arange(len(pFit))
  plt.plot(tData, pFit, 'b', ls='--')
plt.subplot(2,2,4)
for i in range(5):
  pFit=Pout_sigmoid_norm[i]
  tData = np.arange(len(pFit))
  plt.plot(tData, pFit, 'b', ls='--')











