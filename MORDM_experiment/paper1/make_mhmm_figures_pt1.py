import numpy as np
from hmmlearn import hmm
import pandas as pd
from random import random
import seaborn as sns 
from matplotlib import ticker
from matplotlib import pyplot as plt
import math
from scipy import stats as ss
import matplotlib.transforms as mtransforms
import statsmodels.api as sm


###############################################Step 1: Fit mult-site HMM #################################################################################### 


AnnualQ = pd.read_csv('./mhmm_data/historical_annual_streamflow_all_locations.csv')
 
# log transform the mhmm_data
logAnnualQ = np.log(AnnualQ)

np.save('./mhmm_data/logAnnualQ.npy',logAnnualQ)


# initialize matrices to store moments, transition probabilities, 
# stationary distribution and quantiles of Gaussian HMM for each site
nSites = np.shape(logAnnualQ)[1]
nYears=np.shape(logAnnualQ)[0]


# fit hmm model to the mhmm_dataset
hmm_model = hmm.GMMHMM(n_components=2, n_iter=1000,covariance_type='full').fit(logAnnualQ)

#Pull out some model parameters
mus = np.array(hmm_model.means_)
weights=np.array(hmm_model.weights_)
P = np.array(hmm_model.transmat_)
hidden_states = hmm_model.predict(logAnnualQ)


#Dry state doesn't always come first,but we want it to be, so flip if it isn't

if mus[0][0][0] > mus[1][0][0]:
        mus = np.flipud(mus)
        P = np.fliplr(np.flipud(P))
        covariance_matrix_dry=hmm_model.covars_[[1]].reshape(nSites,nSites)
        covariance_matrix_wet=hmm_model.covars_[[0]].reshape(nSites,nSites)
        hidden_states=1-hidden_states
else:
        covariance_matrix_dry=hmm_model.covars_[[0]].reshape(nSites,nSites)
        covariance_matrix_wet=hmm_model.covars_[[1]].reshape(nSites,nSites)        

#Redefine variables
dry_state_means=mus[0,:]
wet_state_means=mus[1,:]
transition_matrix=P



np.save('./mhmm_data/dry_state_means.npy',dry_state_means)
np.save('./mhmm_data/wet_state_means.npy',wet_state_means)
np.save('./mhmm_data/covariance_matrix_dry.npy',covariance_matrix_dry)
np.save('./mhmm_data/covariance_matrix_wet.npy',covariance_matrix_wet)
np.save('./mhmm_data/transition_matrix.npy',transition_matrix)
np.save('./mhmm_data/hidden_states.npy',hidden_states)
np.save('./mhmm_data/mus.npy',mus)




# calculate stationary distribution to determine unconditional probabilities 
eigenvals, eigenvecs = np.linalg.eig(np.transpose(transition_matrix))
one_eigval = np.argmin(np.abs(eigenvals-1))
pi = eigenvecs[:,one_eigval] / np.sum(eigenvecs[:,one_eigval])
unconditional_dry=pi[0]
unconditional_wet=pi[1]


np.save('./mhmm_data/pi.npy',pi)



#Determine the number of years to simulate 
logAnnualQ_s=np.zeros([np.shape(logAnnualQ)[0],nSites])

states = np.empty([np.shape(logAnnualQ)[0]])
if random() <= unconditional_dry:
    states[0] = 0
    logAnnualQ_s[0,:]=np.random.multivariate_normal(np.reshape(dry_state_means,-1),covariance_matrix_dry)
else:
    states[0] = 1
    logAnnualQ_s[0,:] =np.random.multivariate_normal(np.reshape(wet_state_means,-1),covariance_matrix_wet)
    
# generate remaining state trajectory and log space flows
for j in range(1,np.shape(logAnnualQ)[0]):
    if random() <= transition_matrix[int(states[j-1]),int(states[j-1])]:
        states[j] = states[j-1]
    else:
        states[j] = 1 - states[j-1]
        
    if states[j] == 0:
        logAnnualQ_s[j,:] = np.random.multivariate_normal(np.reshape(dry_state_means,-1),covariance_matrix_dry)
    else:
        logAnnualQ_s[j,:] = np.random.multivariate_normal(np.reshape(wet_state_means,-1),covariance_matrix_wet)
    


np.save("./mhmm_data/logAnnualQ_s.npy",logAnnualQ_s)
    

AnnualQ_s = np.exp(logAnnualQ_s)  


np.save("./mhmm_data/AnnualQ_s.npy",AnnualQ_s)


############################################################Step 2: Creating Paneled Distribution (Figure S13) ################################################ 


sns.set_style("white")

fig, ax = plt.subplots(5, 3,figsize=(15, 12),constrained_layout =True)

fig.supxlabel('Log Annual FNF (GL/yr)')

fig.supylabel("Probability Density")




masks0 = hidden_states == 0
masks1 = hidden_states == 1



k=0
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

ax[0,0].hist(logQ[masks0],color='r',alpha=0.5,density=True,bins=10)
ax[0,0].hist(logQ[masks1],color='b',alpha=0.5,density=True,bins=10)

x_0 = np.linspace(mus_new[0]-4*sigmas[0], mus_new[0]+4*sigmas[0], 100)
fx_0 = pi[1]*ss.norm.pdf(x_0,mus_new[0],sigmas[0])

x_1 = np.linspace(mus_new[1]-4*sigmas[1], mus_new[1]+4*sigmas[1], 100)
fx_1 = pi[1]*ss.norm.pdf(x_1,mus_new[1],sigmas[1])
   
ax[0,0].plot(x_0, fx_0, c='r', linewidth=2)
ax[0,0].plot(x_1, fx_1, c='b', linewidth=2)
ax[0,0].set_title("ORO")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)

# Set the yaxis major locator using your ticker object. You can also choose the minor
# tick positions with set_minor_locator.
ax[0,0].yaxis.set_major_locator(yticks)
ax[0,0].xaxis.set_major_locator(xticks)
ax[0,0].text(0.05, 0.95, 'a)', transform=ax[0,0].transAxes,
      fontsize=16, fontweight='bold', va='top')

#####################################################################
k=1
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

ax[0,1].hist(logQ[masks0],color='r',alpha=0.5,density=True,bins=10)
ax[0,1].hist(logQ[masks1],color='b',alpha=0.5,density=True,bins=10)

x_0 = np.linspace(mus_new[0]-4*sigmas[0], mus_new[0]+4*sigmas[0], 100)
fx_0 = pi[1]*ss.norm.pdf(x_0,mus_new[0],sigmas[0])

x_1 = np.linspace(mus_new[1]-4*sigmas[1], mus_new[1]+4*sigmas[1], 100)
fx_1 = pi[1]*ss.norm.pdf(x_1,mus_new[1],sigmas[1])
   
ax[0,1].plot(x_0, fx_0, c='r', linewidth=2)
ax[0,1].plot(x_1, fx_1, c='b', linewidth=2)
ax[0,1].set_title("SHA")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)

ax[0,1].yaxis.set_major_locator(yticks)
ax[0,1].xaxis.set_major_locator(xticks)

ax[0,1].text(0.05, 0.95, 'b)', transform=ax[0,1].transAxes,
      fontsize=16, fontweight='bold', va='top')


#####################################################################
k=2
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

ax[0,k].hist(logQ[masks0],color='r',alpha=0.5,density=True,bins=10)
ax[0,k].hist(logQ[masks1],color='b',alpha=0.5,density=True,bins=10)

x_0 = np.linspace(mus_new[0]-4*sigmas[0], mus_new[0]+4*sigmas[0], 100)
fx_0 = pi[1]*ss.norm.pdf(x_0,mus_new[0],sigmas[0])

x_1 = np.linspace(mus_new[1]-4*sigmas[1], mus_new[1]+4*sigmas[1], 100)
fx_1 = pi[1]*ss.norm.pdf(x_1,mus_new[1],sigmas[1])
   
ax[0,k].plot(x_0, fx_0, c='r', linewidth=2)
ax[0,k].plot(x_1, fx_1, c='b', linewidth=2)

ax[0,k].set_title("FOL")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[0,k].yaxis.set_major_locator(yticks)
ax[0,k].xaxis.set_major_locator(xticks)

ax[0,2].text(0.05, 0.95, 'c)', transform=ax[0,2].transAxes,
      fontsize=16, fontweight='bold', va='top')


##################################################################
k=3
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

ax[1,0].hist(logQ[masks0],color='r',alpha=0.5,density=True,bins=10)
ax[1,0].hist(logQ[masks1],color='b',alpha=0.5,density=True,bins=10)

x_0 = np.linspace(mus_new[0]-4*sigmas[0], mus_new[0]+4*sigmas[0], 100)
fx_0 = pi[1]*ss.norm.pdf(x_0,mus_new[0],sigmas[0])

x_1 = np.linspace(mus_new[1]-4*sigmas[1], mus_new[1]+4*sigmas[1], 100)
fx_1 = pi[1]*ss.norm.pdf(x_1,mus_new[1],sigmas[1])
   
ax[1,0].plot(x_0, fx_0, c='r', linewidth=2)
ax[1,0].plot(x_1, fx_1, c='b', linewidth=2)

ax[1,0].set_title("YRS")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[1,0].yaxis.set_major_locator(yticks)
ax[1,0].xaxis.set_major_locator(xticks)


ax[1,0].text(0.05, 0.95, 'd)', transform=ax[1,0].transAxes,
      fontsize=16, fontweight='bold', va='top')




############################################################################
k=4
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

ax[1,1].hist(logQ[masks0],color='r',alpha=0.5,density=True,bins=10)
ax[1,1].hist(logQ[masks1],color='b',alpha=0.5,density=True,bins=10)

x_0 = np.linspace(mus_new[0]-4*sigmas[0], mus_new[0]+4*sigmas[0], 100)
fx_0 = pi[1]*ss.norm.pdf(x_0,mus_new[0],sigmas[0])

x_1 = np.linspace(mus_new[1]-4*sigmas[1], mus_new[1]+4*sigmas[1], 100)
fx_1 = pi[1]*ss.norm.pdf(x_1,mus_new[1],sigmas[1])
   
ax[1,1].plot(x_0, fx_0, c='r', linewidth=2)
ax[1,1].plot(x_1, fx_1, c='b', linewidth=2)

ax[1,1].set_title("MHB")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[1,1].yaxis.set_major_locator(yticks)
ax[1,1].xaxis.set_major_locator(xticks)

ax[1,1].text(0.05, 0.95, 'e)', transform=ax[1,1].transAxes,
      fontsize=16, fontweight='bold', va='top')



##########################################################################
k=5
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

ax[1,2].hist(logQ[masks0],color='r',alpha=0.5,density=True,bins=10)
ax[1,2].hist(logQ[masks1],color='b',alpha=0.5,density=True,bins=10)

x_0 = np.linspace(mus_new[0]-4*sigmas[0], mus_new[0]+4*sigmas[0], 100)
fx_0 = pi[1]*ss.norm.pdf(x_0,mus_new[0],sigmas[0])

x_1 = np.linspace(mus_new[1]-4*sigmas[1], mus_new[1]+4*sigmas[1], 100)
fx_1 = pi[1]*ss.norm.pdf(x_1,mus_new[1],sigmas[1])
   
ax[1,2].plot(x_0, fx_0, c='r', linewidth=2)
ax[1,2].plot(x_1, fx_1, c='b', linewidth=2)

ax[1,2].set_title("PAR")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[1,2].yaxis.set_major_locator(yticks)
ax[1,2].xaxis.set_major_locator(xticks)

ax[1,2].text(0.05, 0.95, 'f)', transform=ax[1,2].transAxes,
      fontsize=16, fontweight='bold', va='top')



#################################################################
k=6
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

ax[2,0].hist(logQ[masks0],color='r',alpha=0.5,density=True,bins=10)
ax[2,0].hist(logQ[masks1],color='b',alpha=0.5,density=True,bins=10)

x_0 = np.linspace(mus_new[0]-4*sigmas[0], mus_new[0]+4*sigmas[0], 100)
fx_0 = pi[1]*ss.norm.pdf(x_0,mus_new[0],sigmas[0])

x_1 = np.linspace(mus_new[1]-4*sigmas[1], mus_new[1]+4*sigmas[1], 100)
fx_1 = pi[1]*ss.norm.pdf(x_1,mus_new[1],sigmas[1])
   
ax[2,0].plot(x_0, fx_0, c='r', linewidth=2)
ax[2,0].plot(x_1, fx_1, c='b', linewidth=2)

ax[2,0].set_title("NHG")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[2,0].yaxis.set_major_locator(yticks)
ax[2,0].xaxis.set_major_locator(xticks)

ax[2,0].text(0.05, 0.95, 'g)', transform=ax[2,0].transAxes,
      fontsize=16, fontweight='bold', va='top')



#####################################################################

k=7
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

ax[2,1].hist(logQ[masks0],color='r',alpha=0.5,density=True,bins=10)
ax[2,1].hist(logQ[masks1],color='b',alpha=0.5,density=True,bins=10)

x_0 = np.linspace(mus_new[0]-4*sigmas[0], mus_new[0]+4*sigmas[0], 100)
fx_0 = pi[1]*ss.norm.pdf(x_0,mus_new[0],sigmas[0])

x_1 = np.linspace(mus_new[1]-4*sigmas[1], mus_new[1]+4*sigmas[1], 100)
fx_1 = pi[1]*ss.norm.pdf(x_1,mus_new[1],sigmas[1])
   
ax[2,1].plot(x_0, fx_0, c='r', linewidth=2)
ax[2,1].plot(x_1, fx_1, c='b', linewidth=2)

ax[2,1].set_title("NML")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[2,1].yaxis.set_major_locator(yticks)
ax[2,1].xaxis.set_major_locator(xticks)

ax[2,1].text(0.05, 0.95, 'h)', transform=ax[2,1].transAxes,
      fontsize=16, fontweight='bold', va='top')



##########################################################################
k=8
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

ax[2,2].hist(logQ[masks0],color='r',alpha=0.5,density=True,bins=10)
ax[2,2].hist(logQ[masks1],color='b',alpha=0.5,density=True,bins=10)

x_0 = np.linspace(mus_new[0]-4*sigmas[0], mus_new[0]+4*sigmas[0], 100)
fx_0 = pi[1]*ss.norm.pdf(x_0,mus_new[0],sigmas[0])

x_1 = np.linspace(mus_new[1]-4*sigmas[1], mus_new[1]+4*sigmas[1], 100)
fx_1 = pi[1]*ss.norm.pdf(x_1,mus_new[1],sigmas[1])
   
ax[2,2].plot(x_0, fx_0, c='r', linewidth=2)
ax[2,2].plot(x_1, fx_1, c='b', linewidth=2)


ax[2,2].set_title("DNP")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[2,2].yaxis.set_major_locator(yticks)
ax[2,2].xaxis.set_major_locator(xticks)

ax[2,2].text(0.05, 0.95, 'i)', transform=ax[2,2].transAxes,
      fontsize=16, fontweight='bold', va='top')


######################################################################
k=9
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

ax[3,0].hist(logQ[masks0],color='r',alpha=0.5,density=True,bins=10)
ax[3,0].hist(logQ[masks1],color='b',alpha=0.5,density=True,bins=10)

x_0 = np.linspace(mus_new[0]-4*sigmas[0], mus_new[0]+4*sigmas[0], 100)
fx_0 = pi[1]*ss.norm.pdf(x_0,mus_new[0],sigmas[0])

x_1 = np.linspace(mus_new[1]-4*sigmas[1], mus_new[1]+4*sigmas[1], 100)
fx_1 = pi[1]*ss.norm.pdf(x_1,mus_new[1],sigmas[1])
   
ax[3,0].plot(x_0, fx_0, c='r', linewidth=2)
ax[3,0].plot(x_1, fx_1, c='b', linewidth=2)

ax[3,0].set_title("EXC")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[3,0].yaxis.set_major_locator(yticks)
ax[3,0].xaxis.set_major_locator(xticks)

ax[3,0].text(0.05, 0.95, 'j)', transform=ax[3,0].transAxes,
      fontsize=16, fontweight='bold', va='top')



############################################################################
k=10
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

ax[3,1].hist(logQ[masks0],color='r',alpha=0.5,density=True,bins=10)
ax[3,1].hist(logQ[masks1],color='b',alpha=0.5,density=True,bins=10)

x_0 = np.linspace(mus_new[0]-4*sigmas[0], mus_new[0]+4*sigmas[0], 100)
fx_0 = pi[1]*ss.norm.pdf(x_0,mus_new[0],sigmas[0])

x_1 = np.linspace(mus_new[1]-4*sigmas[1], mus_new[1]+4*sigmas[1], 100)
fx_1 = pi[1]*ss.norm.pdf(x_1,mus_new[1],sigmas[1])
   
ax[3,1].plot(x_0, fx_0, c='r', linewidth=2)
ax[3,1].plot(x_1, fx_1, c='b', linewidth=2)

ax[3,1].set_title("MIL")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[3,1].yaxis.set_major_locator(yticks)
ax[3,1].xaxis.set_major_locator(xticks)

ax[3,1].text(0.05, 0.95, 'k)', transform=ax[3,1].transAxes,
      fontsize=16, fontweight='bold', va='top')


############################################################################
k=11

logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

ax[3,2].hist(logQ[masks0],color='r',alpha=0.5,density=True,bins=10)
ax[3,2].hist(logQ[masks1],color='b',alpha=0.5,density=True,bins=10)

x_0 = np.linspace(mus_new[0]-4*sigmas[0], mus_new[0]+4*sigmas[0], 100)
fx_0 = pi[1]*ss.norm.pdf(x_0,mus_new[0],sigmas[0])

x_1 = np.linspace(mus_new[1]-4*sigmas[1], mus_new[1]+4*sigmas[1], 100)
fx_1 = pi[1]*ss.norm.pdf(x_1,mus_new[1],sigmas[1])
   
ax[3,2].plot(x_0, fx_0, c='r', linewidth=2)
ax[3,2].plot(x_1, fx_1, c='b', linewidth=2)

ax[3,2].set_title("PFT")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[3,2].yaxis.set_major_locator(yticks)
ax[3,2].xaxis.set_major_locator(xticks)

ax[3,2].text(0.05, 0.95, 'l)', transform=ax[3,2].transAxes,
      fontsize=16, fontweight='bold', va='top')


##############################################################################
k=12

logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

ax[4,0].hist(logQ[masks0],color='r',alpha=0.5,density=True,bins=10)
ax[4,0].hist(logQ[masks1],color='b',alpha=0.5,density=True,bins=10)

x_0 = np.linspace(mus_new[0]-4*sigmas[0], mus_new[0]+4*sigmas[0], 100)
fx_0 = pi[1]*ss.norm.pdf(x_0,mus_new[0],sigmas[0])

x_1 = np.linspace(mus_new[1]-4*sigmas[1], mus_new[1]+4*sigmas[1], 100)
fx_1 = pi[1]*ss.norm.pdf(x_1,mus_new[1],sigmas[1])
   
ax[4,0].plot(x_0, fx_0, c='r', linewidth=2)
ax[4,0].plot(x_1, fx_1, c='b', linewidth=2)

ax[4,0].set_title("KWH")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[4,0].yaxis.set_major_locator(yticks)
ax[4,0].xaxis.set_major_locator(xticks)

ax[4,0].text(0.05, 0.95, 'm)', transform=ax[4,0].transAxes,
      fontsize=16, fontweight='bold', va='top')

########################################################################

k=13

logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

ax[4,1].hist(logQ[masks0],color='r',alpha=0.5,density=True,bins=10)
ax[4,1].hist(logQ[masks1],color='b',alpha=0.5,density=True,bins=10)

x_0 = np.linspace(mus_new[0]-4*sigmas[0], mus_new[0]+4*sigmas[0], 100)
fx_0 = pi[1]*ss.norm.pdf(x_0,mus_new[0],sigmas[0])

x_1 = np.linspace(mus_new[1]-4*sigmas[1], mus_new[1]+4*sigmas[1], 100)
fx_1 = pi[1]*ss.norm.pdf(x_1,mus_new[1],sigmas[1])
   
ax[4,1].plot(x_0, fx_0, c='r', linewidth=2)
ax[4,1].plot(x_1, fx_1, c='b', linewidth=2)

ax[4,1].set_title("SUC")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[4,1].yaxis.set_major_locator(yticks)
ax[4,1].xaxis.set_major_locator(xticks)


ax[4,1].text(0.05, 0.95, 'n)', transform=ax[4,1].transAxes,
      fontsize=16, fontweight='bold', va='top')

######################################################################


k=14
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

ax[4,2].hist(logQ[masks0],color='r',alpha=0.5,density=True,bins=10)
ax[4,2].hist(logQ[masks1],color='b',alpha=0.5,density=True,bins=10)

x_0 = np.linspace(mus_new[0]-4*sigmas[0], mus_new[0]+4*sigmas[0], 100)
fx_0 = pi[1]*ss.norm.pdf(x_0,mus_new[0],sigmas[0])

x_1 = np.linspace(mus_new[1]-4*sigmas[1], mus_new[1]+4*sigmas[1], 100)
fx_1 = pi[1]*ss.norm.pdf(x_1,mus_new[1],sigmas[1])
   
ax[4,2].plot(x_0, fx_0, c='r', linewidth=2, label='Dry State')
ax[4,2].plot(x_1, fx_1, c='b', linewidth=2,label='Wet State')


ax[4,2].set_title("ISB")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[4,2].yaxis.set_major_locator(yticks)
ax[4,2].xaxis.set_major_locator(xticks)



ax[4,2].text(0.05, 0.95, 'o)', transform=ax[4,2].transAxes,
      fontsize=16, fontweight='bold', va='top')

handles, labels = ax[4,2].get_legend_handles_labels()
fig.legend(handles, labels, loc='lower right', frameon=False, ncol=2)

fig.savefig('./figs/wet_dry_distributions.png',dpi=300)
# fig.savefig('./figs/wet_dry_distributions.pdf')


########################################Step 3: Creating QQ Plot (Figure S14) ########################################################################

fig, ax = plt.subplots(5, 3,figsize=(15, 14),constrained_layout =True)


fig.supxlabel('Observed Quantiles\n Log Annual FNF (GL/yr)')

fig.supylabel('Theoretical Quantiles\n Log Annual FNF (GL/yr)')


masks0 = hidden_states == 0
masks1 = hidden_states == 1


k=0
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

x0_sorted = np.sort(logQ[masks0])
p0_observed = np.arange(1,len(x0_sorted)+1,1)/(len(x0_sorted)+1)
x0_fitted = ss.norm.ppf(p0_observed,mus_new[0],sigmas[0])

x1_sorted = np.sort(logQ[masks1])
p1_observed = np.arange(1,len(x1_sorted)+1,1)/(len(x1_sorted)+1)
x1_fitted = ss.norm.ppf(p1_observed,mus_new[1],sigmas[1])

minimum = np.min([np.min(logQ),np.min(x0_fitted),np.min(x1_fitted)])
maximum = np.max([np.max(logQ),np.max(x0_fitted),np.max(x1_fitted)])

ax[0,0].scatter(x0_sorted,x0_fitted,c='r')
ax[0,0].scatter(x1_sorted,x1_fitted,c='b')
ax[0,0].plot([minimum,maximum],[minimum,maximum],c='k')
ax[0,0].tick_params(axis='both',labelsize=14)
ax[0,0].set_title("ORO")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)

# Set the yaxis major locator using your ticker object. You can also choose the minor
# tick positions with set_minor_locator.
ax[0,0].yaxis.set_major_locator(yticks)
ax[0,0].xaxis.set_major_locator(xticks)
ax[0,0].text(0.05, 0.95, 'a)', transform=ax[0,0].transAxes,
      fontsize=16, fontweight='bold', va='top')

#####################################################################
k=1
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

x0_sorted = np.sort(logQ[masks0])
p0_observed = np.arange(1,len(x0_sorted)+1,1)/(len(x0_sorted)+1)
x0_fitted = ss.norm.ppf(p0_observed,mus_new[0],sigmas[0])

x1_sorted = np.sort(logQ[masks1])
p1_observed = np.arange(1,len(x1_sorted)+1,1)/(len(x1_sorted)+1)
x1_fitted = ss.norm.ppf(p1_observed,mus_new[1],sigmas[1])

minimum = np.min([np.min(logQ),np.min(x0_fitted),np.min(x1_fitted)])
maximum = np.max([np.max(logQ),np.max(x0_fitted),np.max(x1_fitted)])

ax[0,1].scatter(x0_sorted,x0_fitted,c='r')
ax[0,1].scatter(x1_sorted,x1_fitted,c='b')
ax[0,1].plot([minimum,maximum],[minimum,maximum],c='k')
ax[0,1].tick_params(axis='both',labelsize=14)

ax[0,1].set_title("SHA")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)

ax[0,1].yaxis.set_major_locator(yticks)
ax[0,1].xaxis.set_major_locator(xticks)

ax[0,1].text(0.05, 0.95, 'b)', transform=ax[0,1].transAxes,
      fontsize=16, fontweight='bold', va='top')


#####################################################################
k=2
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

x0_sorted = np.sort(logQ[masks0])
p0_observed = np.arange(1,len(x0_sorted)+1,1)/(len(x0_sorted)+1)
x0_fitted = ss.norm.ppf(p0_observed,mus_new[0],sigmas[0])

x1_sorted = np.sort(logQ[masks1])
p1_observed = np.arange(1,len(x1_sorted)+1,1)/(len(x1_sorted)+1)
x1_fitted = ss.norm.ppf(p1_observed,mus_new[1],sigmas[1])

minimum = np.min([np.min(logQ),np.min(x0_fitted),np.min(x1_fitted)])
maximum = np.max([np.max(logQ),np.max(x0_fitted),np.max(x1_fitted)])

ax[0,2].scatter(x0_sorted,x0_fitted,c='r')
ax[0,2].scatter(x1_sorted,x1_fitted,c='b')
ax[0,2].plot([minimum,maximum],[minimum,maximum],c='k')
ax[0,2].tick_params(axis='both',labelsize=14)

ax[0,k].set_title("FOL")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[0,k].yaxis.set_major_locator(yticks)
ax[0,k].xaxis.set_major_locator(xticks)

ax[0,2].text(0.05, 0.95, 'c)', transform=ax[0,2].transAxes,
      fontsize=16, fontweight='bold', va='top')


##################################################################
k=3
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

x0_sorted = np.sort(logQ[masks0])
p0_observed = np.arange(1,len(x0_sorted)+1,1)/(len(x0_sorted)+1)
x0_fitted = ss.norm.ppf(p0_observed,mus_new[0],sigmas[0])

x1_sorted = np.sort(logQ[masks1])
p1_observed = np.arange(1,len(x1_sorted)+1,1)/(len(x1_sorted)+1)
x1_fitted = ss.norm.ppf(p1_observed,mus_new[1],sigmas[1])

minimum = np.min([np.min(logQ),np.min(x0_fitted),np.min(x1_fitted)])
maximum = np.max([np.max(logQ),np.max(x0_fitted),np.max(x1_fitted)])

ax[1,0].scatter(x0_sorted,x0_fitted,c='r')
ax[1,0].scatter(x1_sorted,x1_fitted,c='b')
ax[1,0].plot([minimum,maximum],[minimum,maximum],c='k')
ax[1,0].tick_params(axis='both',labelsize=14)

ax[1,0].set_title("YRS")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[1,0].yaxis.set_major_locator(yticks)
ax[1,0].xaxis.set_major_locator(xticks)


ax[1,0].text(0.05, 0.95, 'd)', transform=ax[1,0].transAxes,
      fontsize=16, fontweight='bold', va='top')




############################################################################
k=4
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

x0_sorted = np.sort(logQ[masks0])
p0_observed = np.arange(1,len(x0_sorted)+1,1)/(len(x0_sorted)+1)
x0_fitted = ss.norm.ppf(p0_observed,mus_new[0],sigmas[0])

x1_sorted = np.sort(logQ[masks1])
p1_observed = np.arange(1,len(x1_sorted)+1,1)/(len(x1_sorted)+1)
x1_fitted = ss.norm.ppf(p1_observed,mus_new[1],sigmas[1])

minimum = np.min([np.min(logQ),np.min(x0_fitted),np.min(x1_fitted)])
maximum = np.max([np.max(logQ),np.max(x0_fitted),np.max(x1_fitted)])

ax[1,1].scatter(x0_sorted,x0_fitted,c='r')
ax[1,1].scatter(x1_sorted,x1_fitted,c='b')
ax[1,1].plot([minimum,maximum],[minimum,maximum],c='k')
ax[1,1].tick_params(axis='both',labelsize=14)


ax[1,1].set_title("MHB")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[1,1].yaxis.set_major_locator(yticks)
ax[1,1].xaxis.set_major_locator(xticks)

ax[1,1].text(0.05, 0.95, 'e)', transform=ax[1,1].transAxes,
      fontsize=16, fontweight='bold', va='top')



##########################################################################
k=5
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

x0_sorted = np.sort(logQ[masks0])
p0_observed = np.arange(1,len(x0_sorted)+1,1)/(len(x0_sorted)+1)
x0_fitted = ss.norm.ppf(p0_observed,mus_new[0],sigmas[0])

x1_sorted = np.sort(logQ[masks1])
p1_observed = np.arange(1,len(x1_sorted)+1,1)/(len(x1_sorted)+1)
x1_fitted = ss.norm.ppf(p1_observed,mus_new[1],sigmas[1])

minimum = np.min([np.min(logQ),np.min(x0_fitted),np.min(x1_fitted)])
maximum = np.max([np.max(logQ),np.max(x0_fitted),np.max(x1_fitted)])

ax[1,2].scatter(x0_sorted,x0_fitted,c='r')
ax[1,2].scatter(x1_sorted,x1_fitted,c='b')
ax[1,2].plot([minimum,maximum],[minimum,maximum],c='k')
ax[1,2].tick_params(axis='both',labelsize=14)

ax[1,2].set_title("PAR")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[1,2].yaxis.set_major_locator(yticks)
ax[1,2].xaxis.set_major_locator(xticks)

ax[1,2].text(0.05, 0.95, 'f)', transform=ax[1,2].transAxes,
      fontsize=16, fontweight='bold', va='top')



#################################################################
k=6
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

x0_sorted = np.sort(logQ[masks0])
p0_observed = np.arange(1,len(x0_sorted)+1,1)/(len(x0_sorted)+1)
x0_fitted = ss.norm.ppf(p0_observed,mus_new[0],sigmas[0])

x1_sorted = np.sort(logQ[masks1])
p1_observed = np.arange(1,len(x1_sorted)+1,1)/(len(x1_sorted)+1)
x1_fitted = ss.norm.ppf(p1_observed,mus_new[1],sigmas[1])

minimum = np.min([np.min(logQ),np.min(x0_fitted),np.min(x1_fitted)])
maximum = np.max([np.max(logQ),np.max(x0_fitted),np.max(x1_fitted)])

ax[2,0].scatter(x0_sorted,x0_fitted,c='r')
ax[2,0].scatter(x1_sorted,x1_fitted,c='b')
ax[2,0].plot([minimum,maximum],[minimum,maximum],c='k')
ax[2,0].tick_params(axis='both',labelsize=14)

ax[2,0].set_title("NHG")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[2,0].yaxis.set_major_locator(yticks)
ax[2,0].xaxis.set_major_locator(xticks)

ax[2,0].text(0.05, 0.95, 'g)', transform=ax[2,0].transAxes,
      fontsize=16, fontweight='bold', va='top')



#####################################################################

k=7
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

x0_sorted = np.sort(logQ[masks0])
p0_observed = np.arange(1,len(x0_sorted)+1,1)/(len(x0_sorted)+1)
x0_fitted = ss.norm.ppf(p0_observed,mus_new[0],sigmas[0])

x1_sorted = np.sort(logQ[masks1])
p1_observed = np.arange(1,len(x1_sorted)+1,1)/(len(x1_sorted)+1)
x1_fitted = ss.norm.ppf(p1_observed,mus_new[1],sigmas[1])

minimum = np.min([np.min(logQ),np.min(x0_fitted),np.min(x1_fitted)])
maximum = np.max([np.max(logQ),np.max(x0_fitted),np.max(x1_fitted)])

ax[2,1].scatter(x0_sorted,x0_fitted,c='r')
ax[2,1].scatter(x1_sorted,x1_fitted,c='b')
ax[2,1].plot([minimum,maximum],[minimum,maximum],c='k')
ax[2,1].tick_params(axis='both',labelsize=14)

ax[2,1].set_title("NML")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[2,1].yaxis.set_major_locator(yticks)
ax[2,1].xaxis.set_major_locator(xticks)

ax[2,1].text(0.05, 0.95, 'h)', transform=ax[2,1].transAxes,
      fontsize=16, fontweight='bold', va='top')



##########################################################################
k=8
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

x0_sorted = np.sort(logQ[masks0])
p0_observed = np.arange(1,len(x0_sorted)+1,1)/(len(x0_sorted)+1)
x0_fitted = ss.norm.ppf(p0_observed,mus_new[0],sigmas[0])

x1_sorted = np.sort(logQ[masks1])
p1_observed = np.arange(1,len(x1_sorted)+1,1)/(len(x1_sorted)+1)
x1_fitted = ss.norm.ppf(p1_observed,mus_new[1],sigmas[1])

minimum = np.min([np.min(logQ),np.min(x0_fitted),np.min(x1_fitted)])
maximum = np.max([np.max(logQ),np.max(x0_fitted),np.max(x1_fitted)])

ax[2,2].scatter(x0_sorted,x0_fitted,c='r')
ax[2,2].scatter(x1_sorted,x1_fitted,c='b')
ax[2,2].plot([minimum,maximum],[minimum,maximum],c='k')
ax[2,2].tick_params(axis='both',labelsize=14)


ax[2,2].set_title("DNP")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[2,2].yaxis.set_major_locator(yticks)
ax[2,2].xaxis.set_major_locator(xticks)

ax[2,2].text(0.05, 0.95, 'i)', transform=ax[2,2].transAxes,
      fontsize=16, fontweight='bold', va='top')


######################################################################
k=9
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

x0_sorted = np.sort(logQ[masks0])
p0_observed = np.arange(1,len(x0_sorted)+1,1)/(len(x0_sorted)+1)
x0_fitted = ss.norm.ppf(p0_observed,mus_new[0],sigmas[0])

x1_sorted = np.sort(logQ[masks1])
p1_observed = np.arange(1,len(x1_sorted)+1,1)/(len(x1_sorted)+1)
x1_fitted = ss.norm.ppf(p1_observed,mus_new[1],sigmas[1])

minimum = np.min([np.min(logQ),np.min(x0_fitted),np.min(x1_fitted)])
maximum = np.max([np.max(logQ),np.max(x0_fitted),np.max(x1_fitted)])

ax[3,0].scatter(x0_sorted,x0_fitted,c='r')
ax[3,0].scatter(x1_sorted,x1_fitted,c='b')
ax[3,0].plot([minimum,maximum],[minimum,maximum],c='k')
ax[3,0].tick_params(axis='both',labelsize=14)

ax[3,0].set_title("EXC")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[3,0].yaxis.set_major_locator(yticks)
ax[3,0].xaxis.set_major_locator(xticks)

ax[3,0].text(0.05, 0.95, 'j)', transform=ax[3,0].transAxes,
      fontsize=16, fontweight='bold', va='top')



############################################################################
k=10
logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

x0_sorted = np.sort(logQ[masks0])
p0_observed = np.arange(1,len(x0_sorted)+1,1)/(len(x0_sorted)+1)
x0_fitted = ss.norm.ppf(p0_observed,mus_new[0],sigmas[0])

x1_sorted = np.sort(logQ[masks1])
p1_observed = np.arange(1,len(x1_sorted)+1,1)/(len(x1_sorted)+1)
x1_fitted = ss.norm.ppf(p1_observed,mus_new[1],sigmas[1])

minimum = np.min([np.min(logQ),np.min(x0_fitted),np.min(x1_fitted)])
maximum = np.max([np.max(logQ),np.max(x0_fitted),np.max(x1_fitted)])

ax[3,1].scatter(x0_sorted,x0_fitted,c='r')
ax[3,1].scatter(x1_sorted,x1_fitted,c='b')
ax[3,1].plot([minimum,maximum],[minimum,maximum],c='k')
ax[3,1].tick_params(axis='both',labelsize=14)

ax[3,1].set_title("MIL")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[3,1].yaxis.set_major_locator(yticks)
ax[3,1].xaxis.set_major_locator(xticks)

ax[3,1].text(0.05, 0.95, 'k)', transform=ax[3,1].transAxes,
      fontsize=16, fontweight='bold', va='top')


############################################################################
k=11

logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

x0_sorted = np.sort(logQ[masks0])
p0_observed = np.arange(1,len(x0_sorted)+1,1)/(len(x0_sorted)+1)
x0_fitted = ss.norm.ppf(p0_observed,mus_new[0],sigmas[0])

x1_sorted = np.sort(logQ[masks1])
p1_observed = np.arange(1,len(x1_sorted)+1,1)/(len(x1_sorted)+1)
x1_fitted = ss.norm.ppf(p1_observed,mus_new[1],sigmas[1])

minimum = np.min([np.min(logQ),np.min(x0_fitted),np.min(x1_fitted)])
maximum = np.max([np.max(logQ),np.max(x0_fitted),np.max(x1_fitted)])

ax[3,2].scatter(x0_sorted,x0_fitted,c='r')
ax[3,2].scatter(x1_sorted,x1_fitted,c='b')
ax[3,2].plot([minimum,maximum],[minimum,maximum],c='k')
ax[3,2].tick_params(axis='both',labelsize=14)

ax[3,2].set_title("PFT")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[3,2].yaxis.set_major_locator(yticks)
ax[3,2].xaxis.set_major_locator(xticks)

ax[3,2].text(0.05, 0.95, 'l)', transform=ax[3,2].transAxes,
      fontsize=16, fontweight='bold', va='top')


##############################################################################
k=12

logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

x0_sorted = np.sort(logQ[masks0])
p0_observed = np.arange(1,len(x0_sorted)+1,1)/(len(x0_sorted)+1)
x0_fitted = ss.norm.ppf(p0_observed,mus_new[0],sigmas[0])

x1_sorted = np.sort(logQ[masks1])
p1_observed = np.arange(1,len(x1_sorted)+1,1)/(len(x1_sorted)+1)
x1_fitted = ss.norm.ppf(p1_observed,mus_new[1],sigmas[1])

minimum = np.min([np.min(logQ),np.min(x0_fitted),np.min(x1_fitted)])
maximum = np.max([np.max(logQ),np.max(x0_fitted),np.max(x1_fitted)])

ax[4,0].scatter(x0_sorted,x0_fitted,c='r')
ax[4,0].scatter(x1_sorted,x1_fitted,c='b')
ax[4,0].plot([minimum,maximum],[minimum,maximum],c='k')
ax[4,0].tick_params(axis='both',labelsize=14)

ax[4,0].set_title("KWH")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[4,0].yaxis.set_major_locator(yticks)
ax[4,0].xaxis.set_major_locator(xticks)

ax[4,0].text(0.05, 0.95, 'm)', transform=ax[4,0].transAxes,
      fontsize=16, fontweight='bold', va='top')

########################################################################

k=13

logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

x0_sorted = np.sort(logQ[masks0])
p0_observed = np.arange(1,len(x0_sorted)+1,1)/(len(x0_sorted)+1)
x0_fitted = ss.norm.ppf(p0_observed,mus_new[0],sigmas[0])

x1_sorted = np.sort(logQ[masks1])
p1_observed = np.arange(1,len(x1_sorted)+1,1)/(len(x1_sorted)+1)
x1_fitted = ss.norm.ppf(p1_observed,mus_new[1],sigmas[1])

minimum = np.min([np.min(logQ),np.min(x0_fitted),np.min(x1_fitted)])
maximum = np.max([np.max(logQ),np.max(x0_fitted),np.max(x1_fitted)])

ax[4,1].scatter(x0_sorted,x0_fitted,c='r')
ax[4,1].scatter(x1_sorted,x1_fitted,c='b')
ax[4,1].plot([minimum,maximum],[minimum,maximum],c='k')
ax[4,1].tick_params(axis='both',labelsize=14)
ax[4,1].set_title("SUC")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[4,1].yaxis.set_major_locator(yticks)
ax[4,1].xaxis.set_major_locator(xticks)


ax[4,1].text(0.05, 0.95, 'n)', transform=ax[4,1].transAxes,
      fontsize=16, fontweight='bold', va='top')

######################################################################


k=14

logQ=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sigmas=(np.array([covariance_matrix_dry[k,k],covariance_matrix_wet[k,k]]))
sigmas=np.sqrt(sigmas)
mus_new=np.log(np.exp(mus[:,0,k])*1.233*math.exp(6)*math.exp(-9))

x0_sorted = np.sort(logQ[masks0])
p0_observed = np.arange(1,len(x0_sorted)+1,1)/(len(x0_sorted)+1)
x0_fitted = ss.norm.ppf(p0_observed,mus_new[0],sigmas[0])

x1_sorted = np.sort(logQ[masks1])
p1_observed = np.arange(1,len(x1_sorted)+1,1)/(len(x1_sorted)+1)
x1_fitted = ss.norm.ppf(p1_observed,mus_new[1],sigmas[1])

minimum = np.min([np.min(logQ),np.min(x0_fitted),np.min(x1_fitted)])
maximum = np.max([np.max(logQ),np.max(x0_fitted),np.max(x1_fitted)])

ax[4,2].scatter(x0_sorted,x0_fitted,c='r',label='Dry State')
ax[4,2].scatter(x1_sorted,x1_fitted,c='b',label='Wet State')
ax[4,2].plot([minimum,maximum],[minimum,maximum],c='k')
ax[4,2].tick_params(axis='both',labelsize=14)

ax[4,2].set_title("ISB")

M = 3
yticks = ticker.MaxNLocator(M)
xticks = ticker.MaxNLocator(M)


ax[4,2].yaxis.set_major_locator(yticks)
ax[4,2].xaxis.set_major_locator(xticks)


handles, labels = ax[4,2].get_legend_handles_labels()
fig.legend(handles, labels, loc='lower right', frameon=False, ncol=2)


ax[4,2].text(0.05, 0.95, 'o)', transform=ax[4,2].transAxes,
      fontsize=16, fontweight='bold', va='top')

fig.savefig('./figs/qqplot.png',dpi=300)
# fig.savefig('./figs/qqplot.pdf')


########################################Step 4: Creating Mosaic Goodness of Fit Plot (Figure S12) ########################################################################

fig, axs = plt.subplot_mosaic([['a)', 'd)'], ['b)', 'd)'], ['c)', 'e)']],
                              constrained_layout=True)


ax = axs['a)']

trans = mtransforms.ScaledTranslation(10/72, -5/72, fig.dpi_scale_trans)
ax.text(0.0, 0.3, 'a)', transform=ax.transAxes + trans,
        fontsize='medium', verticalalignment='top', fontweight='bold')
k=0
Q=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sns.set(font_scale=1.4)
sns.set_style("white")

xs = np.arange(len(Q))+1901
masks = hidden_states == 0
ax.scatter(xs[masks], Q[masks], c='r', label='Dry State')
masks = hidden_states == 1
ax.scatter(xs[masks], Q[masks], c='b', label='Wet State')

ax.plot(xs, Q, c='k')
ax.set_title('ORO')



ax = axs['b)']

trans = mtransforms.ScaledTranslation(10/72, -5/72, fig.dpi_scale_trans)
ax.text(0.0, 0.3, 'b)', transform=ax.transAxes + trans,
        fontsize='medium', verticalalignment='top', fontweight='bold')
k=10
Q=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sns.set(font_scale=1.4)
sns.set_style("white")

xs = np.arange(len(Q))+1901
masks = hidden_states == 0
ax.scatter(xs[masks], Q[masks], c='r', label='Dry State')
masks = hidden_states == 1
ax.scatter(xs[masks], Q[masks], c='b', label='Wet State')

ax.plot(xs, Q, c='k')
 

ax.set_ylabel('Log Annual FNF (GL/yr)')
ax.set_title('MIL')




ax = axs['c)']

trans = mtransforms.ScaledTranslation(10/72, -5/72, fig.dpi_scale_trans)
ax.text(0.0, 0.3, 'c)', transform=ax.transAxes + trans,
        fontsize='medium', verticalalignment='top', fontweight='bold')
k=14
Q=np.log(np.exp(logAnnualQ.iloc[:,k])*1.233*math.exp(6)*math.exp(-9))
sns.set(font_scale=1.4)
sns.set_style("white")

xs = np.arange(len(Q))+1901
masks = hidden_states == 0
ax.scatter(xs[masks], Q[masks], c='r', label='Dry State')
masks = hidden_states == 1
ax.scatter(xs[masks], Q[masks], c='b', label='Wet State')

ax.plot(xs, Q, c='k')
ax.set_title('ISB')
ax.set_xlabel('Year')




ax = axs['d)']

trans = mtransforms.ScaledTranslation(10/72, -5/72, fig.dpi_scale_trans)
ax.text(0.0, 1.0, 'd)', transform=ax.transAxes + trans,
        fontsize='medium', verticalalignment='top', fontweight='bold')

sns.set_style("white")
sm.graphics.tsa.plot_acf(hidden_states,ax=ax,alpha=0.1)
ax.set_xlim([0,10])





ax = axs['e)']
ax.text(0.0, 1.0, 'e)', transform=ax.transAxes + trans,
         fontsize='medium', verticalalignment='top', fontweight='bold')
sm.graphics.tsa.plot_pacf(hidden_states,ax=ax,alpha=0.1)
ax.set_xlim([0,10])
ax.set_ylim([-1,1])
ax.set_xlabel('Lag (years)')
 
fig.set_size_inches([9,7.25])
fig.savefig('./figs/goodness_of_fit.png',dpi=300)
# fig.savefig('./figs/goodness_of_fit.pdf')


