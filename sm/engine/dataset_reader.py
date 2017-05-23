import json
import numpy as np
import logging

from sm.engine.imzml_txt_converter import ImzmlTxtConverter
from sm.engine.util import SMConfig, read_json
from sm.engine.db import DB
from sm.engine.es_export import ESExporter
from sm.engine.work_dir import WorkDirManager


logger = logging.getLogger('sm-engine')


class DatasetReader(object):
    """ Class for reading dataset coordinates and spectra

    Args
    ----------
    id : String
        Dataset id
    input_path : str
        Input path with imzml/ibd files
    sc : pyspark.SparkContext
        Spark context object
    """
    def __init__(self, ds_id, input_path, sc, wd_manager):
        self.ds_id = ds_id
        self.input_path = input_path

        self.sm_config = SMConfig.get_conf()
        self._db = DB(self.sm_config['db'])
        self._wd_manager = wd_manager
        self._sc = sc

        self.coord_pairs = None

    @staticmethod
    def _parse_coord_row(s):
        res = []
        row = s.strip('\n')
        if len(row) > 0:
            vals = row.split(',')
            if len(vals) > 0:
                res = map(int, vals)[1:]
        return res

    def _determine_pixel_order(self):
        coord_path = self._wd_manager.coord_path

        self.coord_pairs = (self._sc.textFile(coord_path)
                            .map(self._parse_coord_row)
                            .filter(lambda t: len(t) == 2).collect())
        self.min_x, self.min_y = np.amin(np.asarray(self.coord_pairs), axis=0)
        self.max_x, self.max_y = np.amax(np.asarray(self.coord_pairs), axis=0)

        _coord = np.array(self.coord_pairs)
        _coord = np.around(_coord, 5)  # correct for numerical precision
        _coord -= np.amin(_coord, axis=0)

        nrows, ncols = self.get_dims()
        pixel_indices = _coord[:, 1] * ncols + _coord[:, 0]
        pixel_indices = pixel_indices.astype(np.int32)
        self._norm_img_pixel_inds = pixel_indices

    def get_norm_img_pixel_inds(self):
        """
        Returns
        -------
        : ndarray
            One-dimensional array of indexes for dataset pixels taken in row-wise manner
        """
        return self._norm_img_pixel_inds

    def get_sample_area_mask(self):
        """
        Returns
        -------
        : ndarray
            One-dimensional bool array of pixel indices where spectra were sampled
        """
        nrows, ncols = self.get_dims()
        sample_area_mask = np.zeros(ncols * nrows).astype(bool)
        sample_area_mask[self._norm_img_pixel_inds] = True
        return sample_area_mask

    def get_dims(self):
        """
        Returns
        -------
        : tuple
            A pair of int values. Number of rows and columns
        """
        return (self.max_y - self.min_y + 1,
                self.max_x - self.min_x + 1)

    def copy_convert_input_data(self):
        if not self._wd_manager.exists(self._wd_manager.txt_path):
            self._wd_manager.copy_input_data(self.input_path)
            imzml_converter = ImzmlTxtConverter(self._wd_manager.local_dir.imzml_path,
                                                self._wd_manager.local_dir.txt_path,
                                                self._wd_manager.local_dir.coord_path)
            imzml_converter.convert()

            if not self._wd_manager.local_fs_only:
                self._wd_manager.upload_to_remote()

        self._determine_pixel_order()

    @staticmethod
    def txt_to_spectrum_non_cum(s):
        arr = s.strip().split("|")
        return int(arr[0]), np.fromstring(arr[1], sep=' ').astype('float32'), np.fromstring(arr[2], sep=' ')

    def get_spectra(self):
        """
        Returns
        -------
        : pyspark.rdd.RDD
            Spark RDD with spectra. One spectrum per RDD entry.
        """
        txt_to_spectrum = self.txt_to_spectrum_non_cum
        logger.info('Converting txt to spectrum rdd from %s', self._wd_manager.txt_path)
        return self._sc.textFile(self._wd_manager.txt_path, minPartitions=8).map(txt_to_spectrum)