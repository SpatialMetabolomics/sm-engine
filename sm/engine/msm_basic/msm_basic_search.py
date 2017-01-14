from sm.engine.msm_basic.formula_imager_segm import compute_sf_images
from sm.engine.msm_basic.formula_img_validator import sf_image_metrics, sf_image_metrics_est_fdr
from sm.engine.search_algorithm import SearchAlgorithm
from sm.engine.util import SMConfig

import logging
import cStringIO
import png
import requests
import numpy as np
from scipy.sparse import coo_matrix


logger = logging.getLogger('sm-engine')


class PngGenerator(object):

    def __init__(self, coords):
        sm_config = SMConfig.get_conf()
        self.upload_uri = sm_config['services']['upload_uri']

        colors = np.array(
            [(68, 1, 84), (68, 2, 85), (68, 3, 87), (69, 5, 88), (69, 6, 90), (69, 8, 91), (70, 9, 92), (70, 11, 94),
             (70, 12, 95), (70, 14, 97), (71, 15, 98), (71, 17, 99), (71, 18, 101), (71, 20, 102), (71, 21, 103),
             (71, 22, 105), (71, 24, 106), (72, 25, 107), (72, 26, 108), (72, 28, 110), (72, 29, 111), (72, 30, 112),
             (72, 32, 113), (72, 33, 114), (72, 34, 115), (72, 35, 116), (71, 37, 117), (71, 38, 118), (71, 39, 119),
             (71, 40, 120), (71, 42, 121), (71, 43, 122), (71, 44, 123), (70, 45, 124), (70, 47, 124), (70, 48, 125),
             (70, 49, 126), (69, 50, 127), (69, 52, 127), (69, 53, 128), (69, 54, 129), (68, 55, 129), (68, 57, 130),
             (67, 58, 131), (67, 59, 131), (67, 60, 132), (66, 61, 132), (66, 62, 133), (66, 64, 133), (65, 65, 134),
             (65, 66, 134), (64, 67, 135), (64, 68, 135), (63, 69, 135), (63, 71, 136), (62, 72, 136), (62, 73, 137),
             (61, 74, 137), (61, 75, 137), (61, 76, 137), (60, 77, 138), (60, 78, 138), (59, 80, 138), (59, 81, 138),
             (58, 82, 139), (58, 83, 139), (57, 84, 139), (57, 85, 139), (56, 86, 139), (56, 87, 140), (55, 88, 140),
             (55, 89, 140), (54, 90, 140), (54, 91, 140), (53, 92, 140), (53, 93, 140), (52, 94, 141), (52, 95, 141),
             (51, 96, 141), (51, 97, 141), (50, 98, 141), (50, 99, 141), (49, 100, 141), (49, 101, 141), (49, 102, 141),
             (48, 103, 141), (48, 104, 141), (47, 105, 141), (47, 106, 141), (46, 107, 142), (46, 108, 142),
             (46, 109, 142), (45, 110, 142), (45, 111, 142), (44, 112, 142), (44, 113, 142), (44, 114, 142),
             (43, 115, 142), (43, 116, 142), (42, 117, 142), (42, 118, 142), (42, 119, 142), (41, 120, 142),
             (41, 121, 142), (40, 122, 142), (40, 122, 142), (40, 123, 142), (39, 124, 142), (39, 125, 142),
             (39, 126, 142), (38, 127, 142), (38, 128, 142), (38, 129, 142), (37, 130, 142), (37, 131, 141),
             (36, 132, 141), (36, 133, 141), (36, 134, 141), (35, 135, 141), (35, 136, 141), (35, 137, 141),
             (34, 137, 141), (34, 138, 141), (34, 139, 141), (33, 140, 141), (33, 141, 140), (33, 142, 140),
             (32, 143, 140), (32, 144, 140), (32, 145, 140), (31, 146, 140), (31, 147, 139), (31, 148, 139),
             (31, 149, 139), (31, 150, 139), (30, 151, 138), (30, 152, 138), (30, 153, 138), (30, 153, 138),
             (30, 154, 137), (30, 155, 137), (30, 156, 137), (30, 157, 136), (30, 158, 136), (30, 159, 136),
             (30, 160, 135), (31, 161, 135), (31, 162, 134), (31, 163, 134), (32, 164, 133), (32, 165, 133),
             (33, 166, 133), (33, 167, 132), (34, 167, 132), (35, 168, 131), (35, 169, 130), (36, 170, 130),
             (37, 171, 129), (38, 172, 129), (39, 173, 128), (40, 174, 127), (41, 175, 127), (42, 176, 126),
             (43, 177, 125), (44, 177, 125), (46, 178, 124), (47, 179, 123), (48, 180, 122), (50, 181, 122),
             (51, 182, 121), (53, 183, 120), (54, 184, 119), (56, 185, 118), (57, 185, 118), (59, 186, 117),
             (61, 187, 116), (62, 188, 115), (64, 189, 114), (66, 190, 113), (68, 190, 112), (69, 191, 111),
             (71, 192, 110), (73, 193, 109), (75, 194, 108), (77, 194, 107), (79, 195, 105), (81, 196, 104),
             (83, 197, 103), (85, 198, 102), (87, 198, 101), (89, 199, 100), (91, 200, 98), (94, 201, 97),
             (96, 201, 96), (98, 202, 95), (100, 203, 93), (103, 204, 92), (105, 204, 91), (107, 205, 89),
             (109, 206, 88), (112, 206, 86), (114, 207, 85), (116, 208, 84), (119, 208, 82), (121, 209, 81),
             (124, 210, 79), (126, 210, 78), (129, 211, 76), (131, 211, 75), (134, 212, 73), (136, 213, 71),
             (139, 213, 70), (141, 214, 68), (144, 214, 67), (146, 215, 65), (149, 215, 63), (151, 216, 62),
             (154, 216, 60), (157, 217, 58), (159, 217, 56), (162, 218, 55), (165, 218, 53), (167, 219, 51),
             (170, 219, 50), (173, 220, 48), (175, 220, 46), (178, 221, 44), (181, 221, 43), (183, 221, 41),
             (186, 222, 39), (189, 222, 38), (191, 223, 36), (194, 223, 34), (197, 223, 33), (199, 224, 31),
             (202, 224, 30), (205, 224, 29), (207, 225, 28), (210, 225, 27), (212, 225, 26), (215, 226, 25),
             (218, 226, 24), (220, 226, 24), (223, 227, 24), (225, 227, 24), (228, 227, 24), (231, 228, 25),
             (233, 228, 25), (236, 228, 26), (238, 229, 27), (241, 229, 28), (243, 229, 30), (246, 230, 31),
             (248, 230, 33), (250, 230, 34), (253, 231, 36)], dtype=np.float) / 256.0
        self.colors = np.c_[colors, np.ones(colors.shape[0])]

        coords = np.array(coords)
        coords -= coords.min(axis=0)
        _ = coords.max(axis=0) + 1
        self.shape = (_[1], _[0])
        rows = coords[:, 1]
        cols = coords[:, 0]
        data = np.ones(coords.shape[0])
        self.mask = coo_matrix((data, (rows, cols)), shape=self.shape).toarray() > 0

    def _get_color_img_data(self, img):
        xa = (((img - img.min()) / (img.max() - img.min())) * 256).astype(int)
        rgba = np.empty(shape=xa.shape + (4,), dtype=self.colors.dtype)
        self.colors.take(xa, axis=0, mode='clip', out=rgba)
        rgba[:, :, 3] = self.mask
        return rgba

    def _generate_png(self, img):
        rgba = self._get_color_img_data(img)
        fp = cStringIO.StringIO()
        png_writer = png.Writer(width=self.shape[1], height=self.shape[0], alpha=True)
        png_writer.write(fp, rgba.reshape(self.shape[0], -1) * 255)
        fp.seek(0)
        return fp

    def save_imgs_as_png(self, imgs):
        imgs += map(lambda _: None, range(4 - len(imgs)))
        uris = []
        for img in imgs:
            if img is None:
                uris.append(None)
            else:
                fp = self._generate_png(img.toarray())
                from requests.adapters import HTTPAdapter
                session = requests.Session()
                session.mount(self.upload_uri, HTTPAdapter(max_retries=5))
                r = session.post(self.upload_uri, files={'iso_image': fp})
                r.raise_for_status()
                uris.append(r.json()['file_uri'])
        return uris


class MSMBasicSearch(SearchAlgorithm):

    def __init__(self, sc, ds, formulas, fdr, ds_config):
        super(MSMBasicSearch, self).__init__(sc, ds, formulas, fdr, ds_config)
        self.metrics = ['chaos', 'spatial', 'spectral']
        self.max_fdr = 0.5

    def search(self):
        logger.info('Running molecule search')
        sf_images = compute_sf_images(self.sc, self.ds, self.formulas.get_sf_peak_df(),
                                      self.ds_config['image_generation']['ppm'])
        all_sf_metrics_df = self.calc_metrics(sf_images)
        sf_metrics_fdr_df = self.estimate_fdr(all_sf_metrics_df)
        sf_metrics_fdr_df = self.filter_sf_metrics(sf_metrics_fdr_df)
        sf_images = self.filter_sf_images(sf_images, sf_metrics_fdr_df)

        png_generator = PngGenerator(self.ds.coords)
        # ion_imgs_url_map = dict(iso_sf_images.mapValues(
        #     lambda imgs: pgn_generator.save_imgs_as_png(imgs)).collect())
        ion_imgs_url_map = dict(map(lambda (k, imgs): (k, png_generator.save_imgs_as_png(imgs)), sf_images.collect()))
        return ion_imgs_url_map

        return sf_metrics_fdr_df,

    def calc_metrics(self, sf_images):
        all_sf_metrics_df = sf_image_metrics(sf_images, self.sc, self.formulas, self.ds, self.ds_config)
        return all_sf_metrics_df

    def estimate_fdr(self, all_sf_metrics_df):
        sf_metrics_fdr_df = sf_image_metrics_est_fdr(all_sf_metrics_df, self.formulas, self.fdr)
        return sf_metrics_fdr_df

    def filter_sf_metrics(self, sf_metrics_df):
        return sf_metrics_df[sf_metrics_df.fdr <= self.max_fdr]
