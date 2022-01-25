'''
    File name: ensembles.py
    Authors: Hoël Seillé / Gerhard Visser
    Date created: 01/10/2020
    Date last modified: 14/04/2021
    Python Version: 3.6
'''
__author__ = "Hoël Seillé / Gerhard Visser"
__copyright__ = "Copyright 2020, CSIRO"
__credits__ = ["Hoël Seillé / Gerhard Visser"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Hoël Seillé"
__email__ = "hoel.seille@csiro.au"
__status__ = "Beta"





# =============================================================================
# Define here the parameters and folders to create the results plots
# =============================================================================

project = 'example'

PlotModels = True
if PlotModels:
    DepthMin = 0
    DepthMax = 1500
    DepthLogScale = False  # plt the depth in log scale

PlotResponses = True
if PlotResponses:
    plotResp_Z = True
    fast_responses_plot = True

Plot_inversionStatistics = True

plot_niblettBostick =False


# =============================================================================
# 
# =============================================================================










import numpy as np
import matplotlib.pyplot as plt
import os
import copy
import sys

sys.path.append("../src")
import ensembles
import MT 
import plotPDFs

files_path = '../projects/%s/transdMT/outfolder'%project

print('Plot models: ',PlotModels)
print('Plot responses: ',PlotResponses)
print('Plot inversion statistics: ', Plot_inversionStatistics)
print('Plot Niblett-Bostick depth-transform: ',plot_niblettBostick)


site_ids = []
for file in os.listdir(files_path):
    if file.endswith(".csv") and not file.endswith("log.csv"):
        site_ids.append(file[:-4])

#print(site_ids)

for site_id in site_ids:             
    
    print('\nMT site %s...'%site_id)
    
    if PlotModels:
        
        samp_models_file =r'%s/%s_sampModels'%(files_path,site_id)

        print('    plotting models ensemble...')

        # load ensemble of models
        ensemble_models, nLayers, lkh, maxLkh_mod, prior  = ensembles.sampModels(samp_models_file)

        #define boundaries of the histogram
        if DepthLogScale:  DepthMax = np.log10(DepthMax); DepthMin=1
        grid_bounds = [-2,6,DepthMin,DepthMax]
        
        #transform resistivities to log10
        LogEnsemble_models = copy.deepcopy(ensemble_models)
        for i in range(len(ensemble_models)):
            LogEnsemble_models[i][:,0] = np.log10(ensemble_models[i][:,0])
            if DepthLogScale:  LogEnsemble_models[i][:,1] = np.log10(ensemble_models[i][:,1])
            
        #compute histograms of the posteriors for the models
        hist_norm_model, stats, chPts = ensembles.histModels(LogEnsemble_models,  
                                                             grid_bounds, 
                                                             nx=100, 
                                                             nz=300)
        #plot PDF model
        plotPDFs.models(site_id,hist_norm_model,grid_bounds,stats, chPts[chPts>10])
        # if DepthLogScale: plt.ylabel('Log$_{10}$ Depth (m)')
        # else: plt.ylabel('Depth (m)')
        plt.savefig('%s/%s_model.png'%(files_path,site_id),dpi=300, bbox_inches="tight")
        plt.close('all')
        



    
    
    
    if PlotResponses:

        #==============================================================================
        # # PDF RESPONSES
        #==============================================================================

        print('    plotting response ensemble...')

        # read input data
        dat_file = r'%s/%s.csv'%(files_path,site_id)
        obs_dat = ensembles.inputData(dat_file, appres=False)
        ff = obs_dat[:,0]
        logT= np.log10(1/ff)
        nfreq=len(logT)
        Zr = obs_dat[:,1]
        Zi = obs_dat[:,2]
        dZ = obs_dat[:,3]
        rho, phy, drho, dphy = MT.z2rhophy(ff, Zr, Zi, dZ**2)

        samp_resps_file = r'%s/%s_sampResps'%(files_path,site_id)
        ensemble_resps = ensembles.sampResps(samp_resps_file, ff)
        #grid boundaries ([Tmin,Tmax,Rhomin,Rhomax,Phymin,Phymax,Zmin,Zmax] 
        Tmin=logT.min()
        Tmax=logT.max()
        grid_bounds_resps = [Tmin-0.0,Tmax+0.0,0,4,0,90,-2,4]    
        
        if not fast_responses_plot and not PlotModels:
            samp_models_file =r'%s/%s_sampModels'%(files_path,site_id)
            ensemble_models, nLayers, lkh, maxLkh_mod, prior  = ensembles.sampModels(samp_models_file)
        
        if not fast_responses_plot:
            if plotResp_Z:
                print('    computing and plotting response PDF...')
                #compute histograms of the posteriors for the responses
                histZr,histZi = ensembles.histResponses(ensemble_models, 
                                                        grid_bounds_resps,
                                                        nRho=300, 
                                                        nT=100, 
                                                        nModels=100,
                                                        datatype='Z')
            else:
                print('    computing and plotting response PDF...')
                #compute histograms of the posteriors for the responses
                histRho,histPhy = ensembles.histResponses(ensemble_models, 
                                                            grid_bounds_resps,
                                                            nRho=300, 
                                                            nT=100, 
                                                            nModels=100,
                                                            datatype='rhoPhy')

        fig = plt.figure(2, figsize=(4,5))
        
        plt.subplot(7,1,(1,3))
        if not fast_responses_plot:
            if plotResp_Z:
                plotPDFs.responses(site_id,histZr,grid_bounds_resps, 
                                   datatype = 'Z')
                logERR = ((np.log10(Zr+dZ)-np.log10(Zr-dZ)))*0.5
                plt.errorbar(logT, np.log10(Zr), yerr = logERR, 
                         fmt='ko',zorder=32, elinewidth=0.7,
                         markersize=1, capsize=1)
            else:
                plotPDFs.responses(site_id,histRho,grid_bounds_resps, 
                                   datatype = 'rho')
                logERR = ((np.log10(rho+drho)-np.log10(rho-drho)))*0.5
                plt.errorbar(logT, np.log10(rho), yerr = logERR, 
                             fmt='ko',zorder=32, elinewidth=0.7,
                             markersize=1, capsize=1)
        else:
            if plotResp_Z:
                plotPDFs.responses_fast(site_id, ff, ensemble_resps, 
                                    datatype='Zr')
                logERR = ((np.log10(Zr+dZ)-np.log10(Zr-dZ)))*0.5
                plt.errorbar(logT, np.log10(Zr), yerr = logERR, 
                         fmt='ko',zorder=32, elinewidth=0.7,
                         markersize=1, capsize=1)
            else:
                plotPDFs.responses_fast(site_id, ff, ensemble_resps, 
                                    datatype='rho')
                logERR = ((np.log10(rho+drho)-np.log10(rho-drho)))*0.5
                plt.errorbar(logT, np.log10(rho), yerr = logERR, 
                             fmt='ko',zorder=32, elinewidth=0.7,
                             markersize=1, capsize=1)



        
        if not fast_responses_plot:
            if plotResp_Z:
                plotPDFs.responses(site_id,histZi,grid_bounds_resps, 
                                   datatype = 'Z')
                logERR = ((np.log10(Zi+dZ)-np.log10(Zi-dZ)))*0.5
                plt.errorbar(logT, np.log10(Zi), yerr = logERR, 
                             fmt='ko',zorder=32, elinewidth=0.7,
                             markersize=1, capsize=1)
            else:
                plt.subplot(7,1,(4,5))
                plotPDFs.responses(site_id,histPhy,grid_bounds_resps, 
                                   datatype = 'phy')
                plt.errorbar(logT, phy, yerr = dphy, 
                             fmt='ko',zorder=32, elinewidth=0.7,
                             markersize=1, capsize=1)
        else:
            if plotResp_Z:
                plotPDFs.responses_fast(site_id, ff, ensemble_resps, 
                                    datatype='Zi')
                logERR = ((np.log10(Zi+dZ)-np.log10(Zi-dZ)))*0.5
                plt.errorbar(logT, np.log10(Zi), yerr = logERR, 
                             fmt='ko',zorder=32, elinewidth=0.7,
                             markersize=1, capsize=1)
            else:
                plt.subplot(7,1,(4,5))
                plotPDFs.responses_fast(site_id, ff, ensemble_resps, 
                                    datatype='phy')
                plt.errorbar(logT, phy, yerr = dphy, 
                             fmt='ko',zorder=32, elinewidth=0.7,
                             markersize=1, capsize=1)

        
        if plot_niblettBostick:
            ax=plt.subplot(7,1,(6,7))
            rho_nb, depth_nb = MT.niblettBostick_depthTransform(rho, phy, 1/ff)
            #plt.loglog(depth_nb, rho_nb,'ko')
            plt.semilogy(logT, depth_nb,'k.')
            #plt.plot( np.log10(rho_nb),-depth_nb,'ko')
            plt.grid(linestyle=':')
            plt.ylabel('Depth (m)');plt.ylim([1, 2*depth_nb[-1]])
            plt.xlabel('Log$_{10}$ Period (sec)')
            plt.yticks([10,100,1000,10000,100000])
            plt.colorbar(ticks=[],drawedges=False, shrink=0.001)
            plt.title('Niblett-Bostick Depth Transform',fontsize=12)
            
            plt.ylim(10,100000)
            plt.xticks(np.arange(-5,5))
            plt.xlim(grid_bounds_resps[0],grid_bounds_resps[1])
        else: 
            plt.xlabel('Log$_{10}$ Period (sec)')
            
        
        plt.tight_layout() 
        plt.savefig('%s/%s_fit.png'%(files_path,site_id),dpi=300, bbox_inches="tight")
        plt.close('all')


    #==============================================================================
    # # INVERSION STATISTICS
    #==============================================================================

    if Plot_inversionStatistics:

        print('    plotting MCMC statistics...')
        
        params_file = './inversionParameters.txt'
        nChains, nIt, samples_perChain, rhoMin, rhoMax = ensembles.read_invParams(params_file)

        try:
            nLayers
        except NameError:
            samp_models_file =r'%s/%s_sampModels'%(files_path,site_id)
            print('\nMT site %s...'%site_id)
            print('    loading models ensemble...')
            # load ensemble of models
            ensemble_models, nLayers, lkh, maxLkh_mod, prior  = ensembles.sampModels(samp_models_file)

        try:
            ensemble_resps
        except NameError:
            # read input data
            dat_file = r'%s/%s.csv'%(files_path,site_id)
            obs_dat = ensembles.inputData(dat_file, appres=False)
            ff = obs_dat[:,0]
            logT= np.log10(1/ff)
            nfreq=len(logT)
            rho, phy, drho, dphy = MT.z2rhophy(obs_dat[:,0],obs_dat[:,1],
                                               obs_dat[:,2],obs_dat[:,3]**2)
            samp_resps_file = r'%s/%s_sampResps'%(files_path,site_id)
            ensemble_resps = ensembles.sampResps(samp_resps_file, ff)

        
        #n_maxChains = 20
        it_num = np.linspace(0.75 * nIt, nIt, samples_perChain,dtype=int)

        fig = plt.figure(10,figsize=(10,7),constrained_layout=False)
        from matplotlib.gridspec import GridSpec
        gs = GridSpec(3, 6, figure=fig)
        ax1 = fig.add_subplot(gs[0, :4])
        ax2 = fig.add_subplot(gs[0, 4:])
        ax3 = fig.add_subplot(gs[1, :4])
        ax4 = fig.add_subplot(gs[1, 4:])
        ax5 = fig.add_subplot(gs[2, :4])
        ax6 = fig.add_subplot(gs[2, 4:])


        rms=[]
        for mod in range(len(ensemble_resps)):
            Zr = ensemble_resps[mod][:,0]
            Zi = ensemble_resps[mod][:,1]
            resp = np.array([Zr.T,Zi.T]).T
            rms.append(MT.rms(obs_dat,resp))


        for i in range(1,nChains):
            for j in range(1,nChains):
                ax1.plot(it_num, rms[i*samples_perChain:(i+1)*samples_perChain], '-', lw=0.1)
        ax1.set_xlim([0.75 * nIt, nIt])
        ax1.axhline(np.median(rms), c = 'r', ls = '--', 
                    label = 'median = %2.2f'%np.median(rms), alpha=0.4)
        ax1.set_ylabel('RMS\n ')
        ax1.set_title('MT site %s - MCMC Post Burn-in Statistics - %d chains'%(site_id, nChains))
        ax1.legend(loc=1)
        
        weights = np.ones_like(rms) / len(rms)
        ax2.hist(rms,20,
                 color='k', 
                 histtype='bar', 
                 ec='white',
                 align='left', 
                 weights=weights)
        ax2.axvline(np.median(rms), c = 'r', ls = '--',label = 'median')
        ax2.set_xlabel('RMS')
        ax2.set_ylabel('probability')
        # ax2.legend(loc=1)

        for i in range(1,nChains):
            for j in range(1,nChains):
                ax3.plot(it_num, 
                         lkh[i*samples_perChain:(i+1)*samples_perChain], 
                         '-', lw=0.1)
        ax3.set_xlim([0.75 * nIt, nIt])
        ax3.axhline(np.median(lkh), c = 'r', ls = '--', 
                    label = 'median = %2.2f'%np.median(lkh), alpha=0.4)
        ax3.set_ylabel('Normalized\nLog Likelihood')
        ax3.legend(loc=1)
        
        weights = np.ones_like(lkh) / len(lkh)
        ax4.hist(lkh,len(np.arange(np.array(lkh).min()-1, np.array(lkh).max()+1, 1))-2,
                 color='k', 
                 histtype='bar', 
                 ec='white',
                 align='left', 
                 weights=weights)
        ax4.axvline(np.median(lkh), c = 'r', ls = '--',label = 'median')
        ax4.set_xlabel('Normalized Log Likelihood')
        ax4.set_ylabel('probability')
        # ax4.legend(loc=1)
        
        for i in range(1,nChains):
            for j in range(1,nChains):
                ax5.plot(it_num, 
                         nLayers[i*samples_perChain:(i+1)*samples_perChain], 
                         '-', lw=0.1)
        ax5.set_xlim([0.75 * nIt, nIt])
        ax5.axhline(np.median(nLayers), c = 'r', ls = '--', 
            label = 'median = %d'%np.median(nLayers), alpha=0.4)
        ax5.set_ylabel('Number of\nlayers')
        ax5.set_xlabel('Iterations')
        ax5.legend(loc=1)

        weights = np.ones_like(nLayers) / len(nLayers)
        ax6.hist(nLayers,len(np.arange(np.array(nLayers).min()-1,
                                       np.array(nLayers).max()+1, 1))-2,
                 color='k', 
                 histtype='bar', 
                 ec='white',
                 align='left', 
                 weights=weights)
        ax6.axvline(np.median(nLayers), c = 'r', ls = '--',label = 'median')
        ax6.set_xlabel('# layers')
        ax6.set_ylabel('probability')
        # ax6.legend(loc=1)

        plt.tight_layout


        plt.savefig('%s/%s_stats.png'%(files_path,site_id),dpi=300, bbox_inches="tight")
        plt.close('all')