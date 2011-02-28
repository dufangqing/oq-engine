# -*- coding: utf-8 -*-
"""Tokens for KVS keys."""

import openquake.kvs

# hazard tokens
SOURCE_MODEL_TOKEN = 'sources'
GMPE_TOKEN = 'gmpe'
JOB_TOKEN = 'job'
ERF_KEY_TOKEN = 'erf'
MGM_KEY_TOKEN = 'mgm'
HAZARD_CURVE_KEY_TOKEN = 'hazard_curve'
MEAN_HAZARD_CURVE_KEY_TOKEN = 'mean_hazard_curve'
QUANTILE_HAZARD_CURVE_KEY_TOKEN = 'quantile_hazard_curve'
STOCHASTIC_SET_TOKEN = 'ses'
MEAN_HAZARD_MAP_KEY_TOKEN = 'mean_hazard_map'
QUANTILE_HAZARD_MAP_KEY_TOKEN = 'quantile_hazard_map'

# risk tokens
CONDITIONAL_LOSS_KEY_TOKEN = 'LOSS_AT_'
EXPOSURE_KEY_TOKEN = 'ASSET'
GMF_KEY_TOKEN = 'GMF'
LOSS_RATIO_CURVE_KEY_TOKEN = 'LOSS_RATIO_CURVE'
LOSS_CURVE_KEY_TOKEN = 'LOSS_CURVE'
VULNERABILITY_CURVE_KEY_TOKEN = 'VULNERABILITY_CURVE'


def loss_token(poe):
    """ Return a loss token made up of the CONDITIONAL_LOSS_KEY_TOKEN and
    the poe cast to a string """
    return "%s%s" % (CONDITIONAL_LOSS_KEY_TOKEN, str(poe))


def vuln_key(job_id):
    """Generate the key used to store vulnerability curves."""
    return openquake.kvs.generate_product_key(job_id, "VULN_CURVES")


def asset_key(job_id, row, col):
    """ Return an asset key generated by openquake.kvs._generate_key """
    return openquake.kvs.generate_key([job_id, row, col,
            EXPOSURE_KEY_TOKEN])


def loss_ratio_key(job_id, row, col, asset_id):
    """ Return a loss ratio key generated by openquake.kvs.generate_key """
    return openquake.kvs.generate_key([job_id, row, col,
            LOSS_RATIO_CURVE_KEY_TOKEN, asset_id])


def loss_curve_key(job_id, row, col, asset_id):
    """ Return a loss curve key generated by openquake.kvs.generate_key """
    return openquake.kvs.generate_key([job_id, row, col,
            LOSS_CURVE_KEY_TOKEN, asset_id])


def loss_key(job_id, row, col, asset_id, poe):
    """ Return a loss key generated by openquake.kvs.generate_key """
    return openquake.kvs.generate_key([job_id, row, col, loss_token(poe),
            asset_id])


def mean_hazard_curve_key(job_id, site):
    """Return the key used to store a mean hazard curve
    for a single site."""
    return openquake.kvs.generate_key([MEAN_HAZARD_CURVE_KEY_TOKEN,
            job_id, site.longitude, site.latitude])


def quantile_hazard_curve_key(job_id, site, quantile):
    """Return the key used to store a quantile hazard curve
    for a single site."""
    return openquake.kvs.generate_key(
            [QUANTILE_HAZARD_CURVE_KEY_TOKEN,
            job_id, site.longitude, site.latitude,
            str(quantile)])


def mean_hazard_map_key(job_id, site, poe):
    """Return the key used to store the IML used in mean hazard
    maps for a single site."""
    return openquake.kvs.generate_key([MEAN_HAZARD_MAP_KEY_TOKEN,
            job_id, site.longitude, site.latitude,
            str(poe)])


def quantile_hazard_map_key(job_id, site, poe, quantile):
    """Return the key used to store the IML used in quantile
    hazard maps for a single site."""
    return openquake.kvs.generate_key([QUANTILE_HAZARD_MAP_KEY_TOKEN,
            job_id, site.longitude, site.latitude,
            str(poe), str(quantile)])


def quantile_value_from_hazard_curve_key(kvs_key):
    """Extract quantile value from a KVS key for a quantile hazard curve."""
    if extract_product_type_from_kvs_key(kvs_key) == \
        QUANTILE_HAZARD_CURVE_KEY_TOKEN:
        (_part_before, _sep, quantile_str) = kvs_key.rpartition(
            openquake.kvs.KVS_KEY_SEPARATOR)
        return float(quantile_str)
    else:
        return None


def quantile_value_from_hazard_map_key(kvs_key):
    """Extract quantile value from a KVS key for a quantile hazard map node."""
    if extract_product_type_from_kvs_key(kvs_key) == \
        QUANTILE_HAZARD_MAP_KEY_TOKEN:
        (part_before, sep, quantile_str) = kvs_key.rpartition(
            openquake.kvs.KVS_KEY_SEPARATOR)
        return float(quantile_str)
    else:
        return None


def poe_value_from_hazard_map_key(kvs_key):
    """Extract PoE value (as float) from a KVS key for a hazard map.
    """

    if extract_product_type_from_kvs_key(kvs_key) in (
        MEAN_HAZARD_MAP_KEY_TOKEN, QUANTILE_HAZARD_MAP_KEY_TOKEN):

        # the PoE is the fifth component of the key, after product
        # token, job ID, site longitude, site latitude
        return float(kvs_key.split(openquake.kvs.KVS_KEY_SEPARATOR)[4])
    else:
        return None


def hazard_curve_key(job_id, realization_num, site_lon, site_lat):
    """ Result a hazard curve key (for a single site) generated by
    openquake.kvs.generate_key """
    return openquake.kvs.generate_key([HAZARD_CURVE_KEY_TOKEN,
                                       job_id,
                                       realization_num,
                                       site_lon,
                                       site_lat])


def realization_value_from_hazard_curve_key(kvs_key):
    """Extract realization value (as string) from a KVS key
    for a hazard curve."""
    if extract_product_type_from_kvs_key(kvs_key) == HAZARD_CURVE_KEY_TOKEN:

        # the realization is the third component of the key, after product
        # token and job ID
        return kvs_key.split(openquake.kvs.KVS_KEY_SEPARATOR)[2]
    else:
        return None


def extract_product_type_from_kvs_key(kvs_key):
    (product_type, sep, part_after) = kvs_key.partition(
        openquake.kvs.KVS_KEY_SEPARATOR)
    return product_type


def gmfs_key(job_id, column, row):
    """Return the key used to store a ground motion field set
    for a single site."""
    return openquake.kvs.generate_product_key(job_id,
            GMF_KEY_TOKEN, column, row)
