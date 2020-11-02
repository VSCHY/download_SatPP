import h5py
import glob
import pandas as pd
import numpy as np
import xarray as xr
import datetime as dt

def get_index(array, value):
    index = np.argmin(abs(array-value))
    return index


def get_limits(vlon, vlat, ilon, flon, ilat, flat):
    '''
    Pedazo de codigo obtenido de Anthony - Practica UNLP.
    ---------
    vlon: 1D array containing the values of longitude
    vlat: 1D array containing the values of latitude
    Values to get the square according to lat-lon values
    ilon: initial longitude
    flon: final longitude
    ilat: initial latitude
    flat: final latitude
    '''
    i0, i1 = np.sort([get_index(vlon, ilon), get_index(vlon, flon)])
    j0, j1 = np.sort([get_index(vlat, ilat), get_index(vlat, flat)])
    i1+=1
    j1+=1

    return i0,i1,j0,j1


def extract_date_f(archivo):
    '''
    Consideramos que los archivos tienen el siguiente nombre:
    late:  3B-HHR-L.MS.MRG.3IMERG.20181120-S073000-E075959.0450.V06B.HDF5
    early: 3B-HHR-E.MS.MRG.3IMERG.20181120-S073000-E075959.0450.V06B.HDF5
    '''
    f1 = archivo.split('/')[-1]
    f1 = f1.split(".")[4]
    f2 = f1.split('-')[0] + f1.split('-')[1]
    
    ff = dt.datetime.strptime(f2, '%Y%m%dS%H%M00')

    return ff


def get_files_from_date(carpeta, fecha):
    '''
    From one date obtains all files related to calculate precipitation between
    12UTC Fecha to 11:30 UTC in Fecha (day+1)
    '''
    from itertools import compress
    #
    d1 = dt.datetime.strptime(fecha, '%Y-%m-%d')
    d1 = d1.replace(hour=12) # 12 UTC
    d2 = d1 + dt.timedelta(days=1)
    d2 = d2.replace(hour=11, minute=30) # 11:30
    str1 = d1.strftime('%Y%m%d')
    str2 = d2.strftime('%Y%m%d')
    l1 = glob.glob(carpeta + '*' + str1 +'*.HDF5')
    l2 = glob.glob(carpeta + '*' + str2 +'*.HDF5')
    fl1 = [extract_date_f(f)>=d1 for f in l1]
    fl2 = [extract_date_f(f)<=d2 for f in l2]
    resultado = list(compress(l1, fl1)) + list(compress(l2, fl2))

    return resultado


def imerg_xarray_from_date(carpeta, fecha, tipo):
    '''
    carpeta: String with the Folder of data is located
    fecha: String with format %Y-%m-%d of date to get extracted
    tipo:
        Early: For GPM Early estimation
        Late: For GPM Late estimation
    '''
    list_files = get_files_from_date(carpeta, fecha)
    if list_files:
        ilon = -75.6; flon = -45.0
        ilat = -57.5; flat = -20.0
        if len(list_files) >=34:  # mas de 70% de datos para el dia, si no NaN
            for iarch, archivo in enumerate(list_files):
                f = h5py.File(archivo, 'r')
                if iarch == 0:
                    g1 = f['Grid']
                    ylat = g1['lat'][:]
                    xlon = g1['lon'][:]
                    pp = g1['precipitationCal'][0,:,:]
                    i0, i1, j0, j1 = get_limits(xlon, ylat, ilon, flon, ilat, flat)
                    lat = ylat[j0:j1]
                    lon = xlon[i0:i1]
                    pp_day = pp[i0:i1,j0:j1]
                else:
                    g1 = f['Grid']
                    pp = g1['precipitationCal'][0,:,:]
                    pp_day += pp[i0:i1,j0:j1]
                f.close()
        else:
            fname_1 = list_files[0].split('/')[-1].split('\\')[-1]
            tiempo = extract_date_f(fname_1)
            texto_1 = ''' #### ----
            Los datos disponibles son menos del 70% para la fecha:
            ''' + tiempo.strftime('%Y-%m-%d') + ' ---- ####'
            print(texto_1)
            f = h5py.File(list_files[0], 'r')
            g1 = f['Grid']
            ylat = g1['lat'][:]
            xlon = g1['lon'][:]
            pp = g1['precipitationCal'][0,:,:]
            i0, i1, j0, j1 = get_limits(xlon, ylat, ilon, flon, ilat, flat)
            lat = ylat[j0:j1]
            lon = xlon[i0:i1]
            pp_day = pp[i0:i1,j0:j1]*np.nan
            f.close()
        # Fin del Loop
        fname = list_files[0].split('/')[-1].split('\\')[-1]
        time = extract_date_f(fname)

        # Start to create an xarray DataArray
        xarlon = xr.IndexVariable("lon", lon, attrs={"unit":"degrees_east","standard_name": "longitude", "long_name" : "longitude", "axis":"X"})
        xarlat = xr.IndexVariable("lat", lat, attrs={"unit":"degrees_north","standard_name": "latitude", "long_name" : "latitude", "axis":"Y"})
        xartime = xr.IndexVariable("time", [dt.datetime(time.year, time.month, time.day, 12,0,0,0)])

        # Why 0.5*pp.day ? 
        pp_day = 0.5*pp_day.T
        pp = np.reshape(pp_day, (1,pp_day.shape[0], pp_day.shape[1]))
        da = xr.DataArray(data=pp, dims=['time','lat', 'lon'],
                          coords={'time': xartime,'lat': xarlat, 'lon': xarlon}, name = "pp")

        if tipo == 'Late':
            da.attrs['title'] = 'GPM-IMERG LateRun'
        elif tipo == 'Early':
            da.attrs['title'] = 'GPM-IMERG EarlyRun'
        else:
            da.attrs['title'] = 'GPM-IMERG Unknown Run'
        da.attrs['long_name'] = '24h accumulated precipitation'
        da.attrs['units'] = 'mm/day'

        global_attrs = {}
        global_attrs["date_created"] = dt.date.today().strftime("%d/%m/%Y")
        global_attrs["comments"] = "Daily Variable calculated from 12UTC-12UTC (+1)"
        ds = xr.Dataset({"pp" : da}, attrs = global_attrs)
        da.close()
        return ds
    else:
        print('#------------------- ERROR -------------------#')
        print('No hay datos para la fecha: ' + fecha)
        print('Terminando el programa')
        exit()


def imerg_xarray_from_mdate(carpeta, fi, fe, tipo):
    '''
    Lo mismo que la funcion anterior pero para
    multiples fechas --> Permite extraer un periodo.
    '''
    a = dt.datetime.strptime(fi, '%Y-%m-%d')
    b = dt.datetime.strptime(fe, '%Y-%m-%d')
    if a < b:
        dias = pd.date_range(start=fi, end=fe)
        da = imerg_xarray_from_date(carpeta, dias[0].strftime('%Y-%m-%d'), tipo)
        nt = len(dias)
        ny = da.values.shape[0]
        nx = da.values.shape[1]
        pp_total = np.empty((nt, ny, nx))
        pp_total[:] = np.nan
        pp_total[0, :, :] = da.values
        lat = da.coords['lat'].values
        lon = da.coords['lon'].values
        da = None
        for it, di in enumerate(dias[1::]):
            fecha = di.strftime('%Y-%m-%d')
            da = imerg_xarray_from_date(carpeta, fecha, tipo)
            pp_total[it + 1, :, :] = da.values
            da = None
        # Finalizamos creando el DataArray Resultado
        df = xr.DataArray(data=0.5*pp_total, dims=['time', 'lat', 'lon'],
                          coords={'time': dias, 'lat': lat, 'lon': lon})
        if tipo == 'Late':
            df.attrs['title'] = 'GPM-IMERG LateRun'
        elif tipo == 'Early':
            df.attrs['title'] = 'GPM-IMERG EarlyRun'
        else:
            df.attrs['title'] = 'GPM-IMERG Unknown Run'
        df.attrs['long_name'] = '24h accumulated precipitation'
        df.attrs['units'] = 'mm/day'

        return df



    else:
        print('### --- --- ###')
        print('Error: la fecha inicial y final no son congruentes:')
        print('Fecha Inicial: ' + fi)
        print('Fecha Final: ' + fe)
        print('### --- --- ###')
        exit()



if __name__ == '__main__':
    import glob
    import os
    import matplotlib.pyplot as plt
    import cartopy
    import cartopy.crs as ccrs
    import cartopy.feature as cpf
    from hidroest_plot import simple_map_plot
    #
    folder = 'e:/GPM-IMERG/prueba-E/'
    file_t = '3B-HHR-L.MS.MRG.3IMERG.20181120-S073000-E075959.0450.V06B.HDF5'
    tfecha = '2018-07-01'
    ffecha = '2019-06-30'
    tipo = 'Early'
    #extract_date_f(file_t)
    df = imerg_xarray_from_mdate(folder, tfecha, ffecha, tipo)
    if os.path.isfile(folder + 'a_GPM-IMERG_EarlyRun.nc'):
        os.remove(folder + 'a_GPM-IMERG_EarlyRun.nc')
    df.to_netcdf(folder + 'a_GPM-IMERG_EarlyRun.nc')
    # -- Codigo para testear como se ve el NetCDF--
    #with xr.open_dataset(folder + 'a_GPM-IMERG_LateRun.nc') as df:
        #print(df.keys())
    #    xlat = df.coords['lat'].values
    #    xlon = df.coords['lon'].values
    #    da = df.to_array().squeeze()
    #    print(da.values.shape)
    #    test_pp = np.nansum(da.values, axis=0)
    # --- figura provisoria ---
    #fig = plt.figure(figsize=(6, 8))
    #proj_lcc = ccrs.PlateCarree()
    #ax = plt.axes(projection=proj_lcc)
    #ax.coastlines(resolution='10m')
    #ax.add_feature(cpf.BORDERS, linestyle='-')
    #ax.contourf(xlon, xlat, test_pp, transform=ccrs.PlateCarree())
    #gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
    #                  linewidth=0.4, color='gray', alpha=0.7, linestyle=':')
    #plt.show()
