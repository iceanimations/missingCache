'''
Created on Oct 20, 2015

@author: qurban.ali
'''
import os
import re
import os.path as osp
import tactic_client_lib as tcl

server = None

def getProjects():
    projects = []
    errors = {}
    if server:
        try:
            projects = server.eval("@GET(sthpw/project.code)")
        except Exception as ex:
            errors['Could not get the list of projects from TACTIC'] = str(ex)
    return projects, errors

def setServer():
    global server
    error = {}
    try:
        server = tcl.TacticServerStub(server='dbserver', login='qurban.ali', password='13490', project='test_mansour_ep')
    except Exception as ex:
        error['Could not connect to TACTIC'] = str(ex)
    return server, error

def setProject(project):
    if server:
        server.set_project(project)
        
parent = None
def setParent(par):
    global parent
    parent = par
    
def setStatus(status):
    if parent:
        parent.setStatus(status)
        parent.processEvents()
        
def setProgressBar(maxVal):
    if parent:
        parent.progressBar.show()
        parent.progressBar.setMaximum(maxVal)
        parent.progressBar.setValue(0)
        parent.processEvents()

def setProgressBarValue(val):
    if parent:
        parent.progressBar.setValue(val)
        parent.processEvents()
        
def unsetProgressBar():
    if parent:
        parent.progressBar.hide()
        parent.progressBar.setValue(0)
        parent.progressBar.setMaximum(0)
        parent.processEvents()
        
def unsetStatus():
    parent.statusLabel.setText('')
    parent.processEvents()

def getShot(shot):
    caches = []
    errors = {}
    cachePath = osp.join(shot, 'animation', 'cache')
    if osp.exists(cachePath):
        cacheFiles = os.listdir(cachePath)
        if cacheFiles:
            for ph in cacheFiles:
                if osp.splitext(ph)[-1] == '.xml':
                    caches.append(ph)
        else:
            errors[cachePath] = 'No cache file found'
    else:
        errors[cachePath] = 'Directory not found'
    return caches, errors
    

def getSeq(seq):
    errors = {}
    caches = {}
    shotsPath = osp.join(seq, 'SHOTS')
    if osp.exists(shotsPath):
        shots = os.listdir(shotsPath)
        if shots:
            setProgressBar(len(shots))
            for i, shot in enumerate(shots):
                shotPath = osp.join(shotsPath, shot)
                if re.search('SH\d+', shot, re.IGNORECASE) and osp.isdir(shotPath):
                    caches[shot], er = getShot(shotPath)
                    errors.update(er)
                setProgressBarValue(i+1)
            unsetProgressBar()
        else:
            errors[seq] = 'No shot found'
    else:
        errors[shotsPath] = 'Directory not found'
    return caches, errors
    
def getCacheFromAsset(meshName, caches, mappedCaches):
    newMeshName = meshName.replace('regular', '').replace('combined', '').replace('shaded', '')
    newMeshName = newMeshName.split('_')
    newMeshName = [x.lower() for x in newMeshName]
    count = 0
    match = None
    for cache in caches:
        newCount = len(set(newMeshName) & set([osp.splitext(x.lower())[0] for x in cache.split('_')]))
        if newCount > count and cache not in mappedCaches:
            match = cache
            count = newCount
    return match

def getAssetsInEpisode(project, epName):
    errors = {}
    assets = {}
    if not server: errors['Server Error'] = 'No TACTIC Server instance found'; return
    if not project: project = server.get_project()
    if not project: errors['Project Error'] = 'Could not find a Project to query data from'; return
    #assetsInEp = server.eval("@SOBJECT(vfx/['episode_code', %s])"%epName.lower())
    #sequences = server.eval("@SOBJECT(vfx/sequence['episode_code', %s])"%epName.lower())
    shots = server.eval("@SOBJECT(vfx/sequence['episode_code', '%s'].vfx/shot)"%epName.lower())
    assetInShot = server.eval("@SOBJECT(vfx/sequence['episode_code', '%s'].vfx/shot.vfx/asset_in_shot)"%epName.lower())
    
    #seqCodes = [seq['code'] for seq in sequences]
    seqCodes = {shot['code']: shot['sequence_code'] for shot in shots}
    
    for asset in assetInShot:
        shotCode = asset['shot_code']
        seqCode = seqCodes[shotCode]
        if assets.has_key(seqCode):
            if assets[seqCode].has_key(shotCode):
                assets[seqCode][shotCode].append(asset['asset_code'])
            else:
                assets[seqCode][shotCode] = [asset['asset_code']]
        else:
            assets[seqCode] = {shotCode: [asset['asset_code']]}
    return assets, errors

def get(project=None, epPath=None):
    errors = {}
    caches = {}
    missing = {}
    extra = {}
    if epPath:
        seqDir = osp.join(epPath, 'SEQUENCES')
        if osp.exists(seqDir):
            seqs = os.listdir(seqDir)
            if seqs:
                seqLen = len(seqs)
                for i, seq in enumerate(seqs):
                    setStatus('Scanning %s (%s of %s)'%(seq, i+1, seqLen))
                    sp = osp.join(seqDir, seq)
                    if re.search('SQ\d+', seq, re.IGNORECASE) and osp.isdir(sp):
                        caches[seq], er = getSeq(sp)
                        errors.update(er)
            else:
                errors[seqDir] = 'No sequence found'
        else:
            errors[seqDir] = 'Directory not found'
        if caches:
            epName = osp.basename(epPath).upper()
            setStatus('Retrieving assets from TACTIC')
            epAssets, er = getAssetsInEpisode(project, epName)
            errors.update(er)
            if epAssets:
                shotCaches = []
                seqLen = len(caches)
                i = 1
                for seqName, shots in caches.items():
                    setStatus('Comparing %s (%s of %s)'%(seqName, i, seqLen))
                    seqCode = '_'.join([epName, seqName])
                    setProgressBar(len(shots))
                    j = 1
                    for shotName, cacheFiles in shots.items():
                        del shotCaches[:]
                        cacheFiles.sort(key=len, reverse=True)
                        shotCode = '_'.join([epName, shotName])
                        shotAssets = epAssets[seqCode][shotCode]
                        shotAssets = [asset.lower() for asset in shotAssets]
                        shotAssets.sort(key=len, reverse=True)
                        cacheFiles = [cacheFile.lower() for cacheFile in cacheFiles]
                        for asset in shotAssets:
                            cache = getCacheFromAsset(asset, cacheFiles, shotCaches)
                            if cache:
                                shotCaches.append(cache)
                            else:
                                if missing.has_key(seqName):
                                    if missing[seqName].has_key(shotName):
                                        missing[seqName][shotName].append(asset)
                                    else:
                                        missing[seqName][shotName] = [asset]
                                else:
                                    missing[seqName] = {shotName: [asset]}
                        temp = list(set(cacheFiles).difference(set(shotCaches)))
                        if temp:
                            if extra.has_key(seqName):
                                if not extra[seqName].has_key(shotName):
                                    extra[seqName][shotName] = temp
                            else:
                                extra[seqName] = {shotName: temp}
                        setProgressBarValue(j)
                        j += 1
                    i += 1
                    unsetProgressBar()
                    unsetStatus()
            else:
                errors['TACTIC'] = 'No assets found in shots'
    return missing, extra, errors