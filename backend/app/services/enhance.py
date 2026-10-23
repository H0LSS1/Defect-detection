"""图像增强算法集

按类别组织为类方法, 每个方法可独立调用与组合; 生产 pipeline 只使用其中一部分。
"""

import cv2
import numpy as np


class ImageEnhancer:
    def __init__(
        self,
        median_ksize: int = 5,
        clahe_clip: float = 2.0,
        clahe_tile: int = 8,
        target_brightness: float = 0.5,
        usm_amount: float = 1.5,
    ):
        self.median_ksize = median_ksize
        self.target_brightness = target_brightness
        self.usm_amount = usm_amount
        self._clahe = cv2.createCLAHE(
            clipLimit=clahe_clip, tileGridSize=(clahe_tile, clahe_tile)
        )

    # ===== 去噪 =====

    def denoise_median(self, img: np.ndarray) -> np.ndarray:
        """中值滤波: 取邻域中位数, 对飞溅/椒盐类孤立噪声最有效."""
        return cv2.medianBlur(img, self.median_ksize)

    def denoise_gaussian(self, img: np.ndarray) -> np.ndarray:
        """高斯滤波: 加权平均平滑, 抑制高频噪声但会糊边."""
        k = self.median_ksize
        return cv2.GaussianBlur(img, (k, k), 0)

    def denoise_bilateral(self, img: np.ndarray) -> np.ndarray:
        """双边滤波: 去噪同时保留边缘, 适合保持缺陷轮廓."""
        return cv2.bilateralFilter(img, 9, 75, 75)

    def denoise_nlm(self, img: np.ndarray) -> np.ndarray:
        """非局部均值(彩色): 去噪效果最强但速度慢, 适合离线处理."""
        return cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)

    # ===== 对比度 / 亮度 =====

    def equalize_ycrcb(self, img: np.ndarray) -> np.ndarray:
        """全局直方图均衡: 只均衡 Y 亮度通道, 整体拉对比度, 弱纹理图可能过度增强."""
        ycc = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        y, cr, cb = cv2.split(ycc)
        y = cv2.equalizeHist(y)
        return cv2.cvtColor(cv2.merge((y, cr, cb)), cv2.COLOR_YCrCb2BGR)

    def clahe_ycrcb(self, img: np.ndarray) -> np.ndarray:
        """自适应限制对比度均衡(CLAHE): 分块均衡并限制放大倍数, 工业检测首选, 不易过曝."""
        ycc = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        y, cr, cb = cv2.split(ycc)
        y = self._clahe.apply(y)
        return cv2.cvtColor(cv2.merge((y, cr, cb)), cv2.COLOR_YCrCb2BGR)

    def gamma_adaptive(self, img: np.ndarray) -> np.ndarray:
        """自适应伽马: 依图像平均亮度求 gamma, 将均值拉向目标亮度."""
        mean = img.mean() / 255.0
        if mean <= 0 or mean >= 1:
            return img
        gamma = np.log10(self.target_brightness) / np.log10(mean)
        return self.gamma_fixed(img, gamma)

    def gamma_fixed(self, img: np.ndarray, gamma: float) -> np.ndarray:
        """固定伽马: 手动指定, gamma<1 提亮暗部 / gamma>1 压暗高光."""
        table = np.array([((i / 255.0) ** gamma) * 255 for i in range(256)]).astype(
            "uint8"
        )
        return cv2.LUT(img, table)

    def linear_stretch(self, img: np.ndarray) -> np.ndarray:
        """线性拉伸: min-max 归一化到 0-255, 低对比度图快速拉满动态范围."""
        lo, hi = img.min(), img.max()
        if hi == lo:
            return img
        return ((img.astype(np.float32) - lo) / (hi - lo) * 255).astype("uint8")

    def percentile_stretch(
        self, img: np.ndarray, low: float = 1.0, high: float = 99.0
    ) -> np.ndarray:
        """百分位截断拉伸: 截掉两端极值后拉伸, 抗飞溅亮点/暗点干扰."""
        lo, hi = np.percentile(img, [low, high])
        if hi <= lo:
            return img
        clipped = np.clip(img.astype(np.float32), lo, hi)
        return ((clipped - lo) / (hi - lo) * 255).astype("uint8")

    def log_transform(self, img: np.ndarray) -> np.ndarray:
        """对数变换: 扩展暗部/压缩高亮, 增强暗区细节."""
        table = np.array(
            [255.0 * np.log1p(i) / np.log1p(255) for i in range(256)]
        ).astype("uint8")
        return cv2.LUT(img, table)

    # ===== 锐化 =====

    def sharpen_usm(self, img: np.ndarray) -> np.ndarray:
        """USM 锐化: 原图与高斯模糊的差值加权叠加, 增强缺陷边缘."""
        blur = cv2.GaussianBlur(img, (0, 0), 3)
        return cv2.addWeighted(img, self.usm_amount, blur, 1 - self.usm_amount, 0)

    def sharpen_laplacian(self, img: np.ndarray) -> np.ndarray:
        """拉普拉斯锐化: 原图叠加二阶导数细节, 增强纹理与边缘."""
        lap = cv2.Laplacian(img, cv2.CV_64F)
        sharp = img.astype(np.float64) - 0.3 * lap
        return np.clip(sharp, 0, 255).astype("uint8")

    # ===== 形态学 =====

    def tophat(self, img: np.ndarray, ksize: int = 15) -> np.ndarray:
        """顶帽: 原图减开运算, 提取比周围亮的细节(亮缺陷/高光飞溅)."""
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
        return cv2.morphologyEx(img, cv2.MORPH_TOPHAT, kernel)

    def blackhat(self, img: np.ndarray, ksize: int = 15) -> np.ndarray:
        """底帽: 闭运算减原图, 提取比周围暗的细节(暗缺陷/裂纹)."""
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
        return cv2.morphologyEx(img, cv2.MORPH_BLACKHAT, kernel)

    def morph_close(self, img: np.ndarray, ksize: int = 3) -> np.ndarray:
        """闭运算: 填充小暗孔与断裂, 平滑目标边界."""
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
        return cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)

    def morph_open(self, img: np.ndarray, ksize: int = 3) -> np.ndarray:
        """开运算: 去除小白点噪声, 保持大目标形状."""
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
        return cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)

    # ===== 组合 pipeline =====

    def enhance(self, img: np.ndarray) -> np.ndarray:
        """生产默认管线: 中值去噪 -> CLAHE -> 自适应伽马."""
        return self.gamma_adaptive(self.clahe_ycrcb(self.denoise_median(img)))
