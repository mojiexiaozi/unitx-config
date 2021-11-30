import logging

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

LOG_SOURCE = 'CUSTOM TCP SERVER'
NG_FUNC_AREA = "功能区"
NG_NOT_FUNC_AREA = "非功能区"
NG_NOT_DEFINE = "NG: 未定义缺陷"


def log_info(msg):
    logger.info(f'{LOG_SOURCE}: {msg}')


def log_error(msg):
    logger.error(f'{LOG_SOURCE}: {msg}')


def log_warn(msg):
    logger.warn(f'{LOG_SOURCE}: {msg}')


class Point(object):
    def __init__(self, x, y) -> None:
        self._x = x
        self._y = y

    def get_pos(self):
        return self._x, self._y

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y


def is_ng_stat(stat):
    return stat['ng']


def filter_ng_stats(network_result):
    if (network_result.ng_stats is None or len(network_result.ng_stats) == 0):
        log_warn("network_result.stats is None or zero length")
        return []

    return list(filter(is_ng_stat, network_result.ng_stats))


def get_rects_from_segment(segment):
    '''从segments数据中获取矩形点+中心点'''
    points = []
    for x_str, y_str in segment["original_mr_box"]:
        points.append(Point(float(x_str), float(y_str)))
    # rects.append(points)

    orgin_x = float(segment['original_x'])
    orgin_y = float(segment['original_y'])
    orgin = Point(orgin_x, orgin_y)
    points.append(orgin)
    return points


def is_points_in_not_func_area(points, X1, X2):
    '''点是否位于非功能区域'''
    for point in points:
        if point.X > X1 and point.X < X2:
            return True
    return False


def check_is_ng_stat(stat, X1, X2, length_threshold, width_threshold, area_threshold):
    segments = stat["segments"]
    for segment in segments:
        original_mr_width = segment["original_mr_width"]
        original_mr_length = segment["original_mr_length"]
        original_area = segment["original_mr_length"]
        points = get_rects_from_segment(segment)
        if not is_points_in_not_func_area(points, X1, X2):
            return True, f"{NG_FUNC_AREA}-{stat['name']}"
        else:
            if original_mr_length > length_threshold or original_mr_width < width_threshold or original_area < area_threshold:
                return True, f"{NG_NOT_FUNC_AREA}-{stat['name']}"


def get_threshold(threshold, repeat_index):
    area_index = repeat_index // 20  # 20张图一个区域
    if area_index == 0:
        return threshold["Photo spot 1 X  left limit"], threshold["Photo spot 1 X  right limit"]
    elif area_index == 1:
        return threshold["Photo spot 2 X  left limit"], threshold["Photo spot 2 X  right limit"]
    elif area_index == 2:
        return threshold["Photo spot 3 X  left limit"], threshold["Photo spot 3 X  right limit"]
    elif area_index == 3:
        return threshold["Photo spot 4 X  left limit"], threshold["Photo spot 4 X  right limit"]


def compute_image_result(image_network_results, threshold):
    area_threshold = threshold("Not func area threshold")
    length_threshold = threshold("Not func length threshold")
    width_threshold = threshold("Not func width threshold")

    ng_types = []
    for key in image_network_results:
        network = image_network_results[key]

        repeat_index = network.repeat_index
        log_info(f"repeat_index:{repeat_index}")
        X1, X2 = get_threshold(threshold, repeat_index)
        ng_stats = filter_ng_stats(network)
        for stat in ng_stats:
            ng, ng_type = check_is_ng_stat(
                stat, X1, X2, length_threshold, width_threshold, area_threshold)

    return len(ng_types) != 0, ng_types
