import os, sys, copy
import numpy as np

"""
**PURPOSE**
    | Python code used for trend estimations 
    | as part of Kevin Gaastra's Postdoctoral work at JPL Oct. 2023-present

**COPYRIGHT**
    | Copyright 2024, by the California Institute of Technology
    | United States Government Sponsorship acknowledged
    | All rights reserved

**AUTHORS**
    | Kevin Gaastra
    | Jet Propulsion Laboratory
    | California Institute of Technology
    | Pasadena, CA, USA
    | Felix Landerer and Munish Sikka added option to exclude trend while constructing the timeseries from model params
"""

#############################Trajectory Modeling Functions
def fit_tsin(time, data, sig=None, poly_deg=1, freq=1, offsets=[], return_amp_phase=False, return_param_unc=False, chi2_cor=True, S2_G_GFO_shift=1):
    """
    Linear regression fitting a polynomial + quasi-periodic function with offsets. freq can be a float if there is one oscillation period with unknown phase
    or a itterable type if there is more than one oscillation contained in the signal such as an annual and half-annual period. All offsets that need to be fit
    must be passed in an itterable type to the offsets kwarg. Default return gives the periodic components of each freq as the amplitude of the sin and cos components each in order
    as it was passed in the freq kwarg.

    Parameters
    ---------------
    time:1dArray - independent variable over which to fit the model
    data:1dArray - dependent variable to be predicted by the model
    sig:1dArray - 1-sigma uncertainties on the dependent variable
    poly_deg:int - integer specifying the degree of the polynomial to fit
    freq:float,iterable - the frequencies of unknown phase and amplitude to fit to the data
    offsets:iterable - locations at which to offset the model by an unknown ammount
    return_amp_phase:bool - return amplitudes and phases for the periodic pieces instead of sin/cos coef. (only supported if return_param_unc=False)
    return_param_unc:bool - return the uncertainties on the fitted parameters
    chi2_cor:bool - correct parameter uncertainties for over-/under-dispursion, should only be False if there is a justification or physical basis for the input data uncertainties that you don't want changed
    
    Returns
    ---------------
    model:1NdArray - array of the coeffecents to the equation: y = sum_i(A_i*sin(w_i*t) + B_i*cos(w_i*t)) + C*t + D + (step size of offsets) of size 2*len(freq)+2+len(offsets)
    sds:1NdArray - array of the standard deviation of the coeffecents of the model, discards covariance (only if return_param_unc=True)
    unused_steps:1NdArray - array of times for offsets that were not used in the inversion. This can happen if more than one significant offset is suggested between two of the same data points.
                            Generally the user should know better than this, but it can happen and makes the data kernal singular so the program will just recognize these and return a list of them.
    """
    if hasattr(freq,"__iter__"): ang_freq = 2*np.pi*np.array(freq)
    else: ang_freq = 2*np.pi*np.array([freq]) #assume that not being iterable means it is a number
    s_alias = 2*np.pi*np.array(365.25/161)
    s_alias_index = -9999
    ph_sh = 100 # days
    ph_sh = ph_sh * 360/365 # change to degrees
    if (s_alias in ang_freq):
        s_alias_index = np.where(ang_freq == s_alias)
    #construct the various pieces of the data kernal (G = f(x)) and construct it and the weight matrix (W = diag(1/sig))
    dheavyside_steps,unused_steps,periodic_coefs,poly_coefs = [],[],[],[]
    #this had more edge cases than I expected, but if the offset suggested is before the timeseries, after the timeseries, or if there are two steps between the same point the data kernal will be singular
    for off in offsets: #Construct offsets
        step = (time>=off).astype(int)
        #checks for steps out of range of independent variable, and check for steps that are duplicated because of user error
        if step.sum()!=len(time) and step.sum()!=0 and (step.sum() not in list(map(sum,dheavyside_steps))): dheavyside_steps.append(step)
        else: unused_steps.append(off)
    for afreq in ang_freq: #construct frequency coef
        if(s_alias_index != -9999 and afreq == s_alias):
            #print(afreq)
            grfo_coefs_cos = np.cos(S2_G_GFO_shift * ph_sh/180*np.pi + afreq * time[163:])
            grfo_coefs_sin = np.sin(S2_G_GFO_shift * ph_sh/180*np.pi + afreq * time[163:])
            grac_coefs_cos = np.cos(afreq*time[:163])
            grac_coefs_sin = np.sin(afreq*time[:163])
            S2_coefs_sin = np.concatenate((grac_coefs_sin, grfo_coefs_sin))
            S2_coefs_cos = np.concatenate((grac_coefs_cos, grfo_coefs_cos))
            periodic_coefs += [S2_coefs_sin,S2_coefs_cos]
        else:
            periodic_coefs += [np.sin(afreq*time),np.cos(afreq*time)]
    for deg in range(poly_deg,-1,-1): #construct the inversion kernal for the polynomial
        poly_coefs.append(time**deg)
    G = np.vstack(periodic_coefs+poly_coefs+dheavyside_steps).T #Construct Data Kernel
    #mess with the sigmas to make sure that there is no divide by zero problem
    if isinstance(sig,type(None)): W,sig = np.eye(len(data)),np.ones(len(data))
    else:
        sig = np.array(sig).astype(np.float64) #ensure there are enough bits for very small sigmas
        sig[np.where(sig<1e-22)] = 1e-8 #float32 smallest is 1e-45 so sqrt of that is ~1e-22 with 1e-12 being more than small enough
        W = np.diag(sig**-2)
    
    #DOOOOO THE INVERSION
    try: model = np.linalg.inv(G.T @ W @ G) @ G.T @ W @ data #y = sum_i(A_i*sin(w_i*t) + B_i*cos(w_i*t)) + C*t + D + (piecewise steps)
    except np.linalg.LinAlgError: raise np.linalg.LinAlgError("Data Kernal + Weights was singular and could not invert. This is likely due to weights too close to zero resulting in infinate values in the matrix inversion, but can be caused by issues in the input time array as well."); import pdb; pdb.set_trace()

    #Calculate var/covar if desired, then toss covar and report sds of parameters
    if return_param_unc:
        #catch underdetermined or even determined case
        if G.shape[0]<=G.shape[1]:
            sds = np.zeros(len(model)).astype(np.float32)
            sds[:] = np.nan
            return model, sds, unused_steps
        #calculate chi2 to correct for over/under dispursion, if the user doesn't like this they can undo it, I'll mention in the doc later
        pre_data = G @ model
        chi2 = np.nansum(((data-pre_data)**2)/(np.array(sig)**2))
        deg_free = (G.shape[0]-G.shape[1]) #data kernal (G) is NxM or data by parameter shape by definition
        chi2_norm = chi2/deg_free
        if not chi2_cor or chi2_norm==0 or np.isnan(chi2_norm): err = sig
        else: err = sig*np.sqrt(chi2_norm) #over/under correction to input sigmas

        alpha = G.T @ np.diag(err**-2) @ G

        #invert alpha to get error matrix which has the varriance of the ith model parameter on it's diagonal as per Bev 8-28
        error_matrix = np.linalg.inv(alpha)
        if (err==np.ones(G.shape[0])).all():
            ss = sum((data-pre_data)**2)/deg_free
            sds = np.sqrt(ss*np.diag(error_matrix))#[::-1]
        else: sds = np.sqrt(np.diag(error_matrix))#[::-1]

        return model, sds, unused_steps

    if return_amp_phase: #change the perodic coeffecents to amp/phase if required
        for i in range(len(ang_freq)):
            model[2*i] = np.sqrt(model[2*i]**2+model[2*i+1]**2)
            model[2*i+1] = np.arctan2(model[2*i],model[2*i+1])

    return model, unused_steps

def get_tsin(model, time, poly_deg=1,exclude_trend = 0, freq=1, offsets=[], is_amp_phase=False, S2_G_GFO_shift=1):
    """
    get_tsin applies a fit_tsin model to a new independant variable (time) domain returning the predicted dependent variable
    freq and offsets must be of the same form as those passed to the original fit_tsin function used to generate the model
    parameters, not doing so will result in an error. Note: an exception is any unused steps returned from fit_tsin
    
    Parameters
    ---------------
    model:1NdArray - array of the coeffecents to the equation: y = sum_i(A_i*sin(w_i*t) + B_i*cos(w_i*t)) + C*t + D + (step size of offsets) of size 2*len(freq)+2+len(offsets)
    time:1dArray - independent variable over which to fit the model
    freq:float,iterable - the frequencies of unknown phase and amplitude to fit to the data
    offsets:iterable - locations at which to offset the model by an unknown ammount
    is_amp_phase:bool - if the model has amplitude and phase instead of A*sin + B*cos values use this flag
    
    Returns
    ---------------
    pre_data:1NdArray - array of the coeffecents to the equation: y = sum_i(A_i*sin(w_i*t) + B_i*cos(w_i*t)) + C*t + D + (step size of offsets) of size 2*len(freq)+2+len(offsets)
    """
    if hasattr(freq,"__iter__"): ang_freq = 2*np.pi*np.array(freq)
    else: ang_freq = 2*np.pi*np.array([freq]) #assume that not being iterable means it is a number
    s_alias = 2*np.pi*np.array(365.25/161)
    s_alias_index = -9999
    ph_sh = 100 # days
    ph_sh = ph_sh * 360/365 # change to degrees
    if (s_alias in ang_freq):
        s_alias_index = np.where(ang_freq == s_alias)
    if is_amp_phase:
        for i in range(len(ang_freq)):
            A = model[2*i]*np.sin(ang_freq+model[2*i+1])
            B = model[2*i]*np.cos(ang_freq-model[2*i+1])
            model[0],model[1] = A,B
    #Assume it is a sequence unless error then try scaler
    dheavyside_steps,periodic_coefs,poly_coefs = [],[],[]
    for off in offsets:
        step = (time>=off).astype(int)
        #checks for steps out of range of independent variable, and check for steps that are duplicated because of user error
        if step.sum()!=len(time) and step.sum()!=0 and (step.sum() not in list(map(sum,dheavyside_steps))): dheavyside_steps.append(step)
    for afreq in ang_freq:
        if(s_alias_index != -9999 and afreq == s_alias):
            grfo_coefs_cos = np.cos(S2_G_GFO_shift * ph_sh/180*np.pi + afreq * time[163:])
            grfo_coefs_sin = np.sin(S2_G_GFO_shift * ph_sh/180*np.pi + afreq * time[163:])
            grac_coefs_cos = np.cos(afreq*time[:163])
            grac_coefs_sin = np.sin(afreq*time[:163])
            S2_coefs_sin = np.concatenate((grac_coefs_sin, grfo_coefs_sin))
            S2_coefs_cos = np.concatenate((grac_coefs_cos, grfo_coefs_cos))
            periodic_coefs += [S2_coefs_sin,S2_coefs_cos]
        else:
            periodic_coefs += [np.sin(afreq*time),np.cos(afreq*time)]
    for deg in range(poly_deg,-1,-1): #construct the inversion kernal for the polynomial
        poly_coefs.append(time**deg)
    if exclude_trend==1 and poly_deg ==0: 
        column_to_remove = len(periodic_coefs)
        model = np.delete(model,[column_to_remove])
    G = np.vstack(periodic_coefs+poly_coefs+dheavyside_steps).T #Construct Data Kernel
    try: return G @ model
    except ValueError: raise ValueError("matmul error: opperands of different length likely due to an incorrect number of offsets provided for the model given. Offsets must be an iterable of length, model length - 4.")
