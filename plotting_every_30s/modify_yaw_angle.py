
def modify_yaw_angle_from_ISO_8855(yaw_angle):
    yaw_angle0 = yaw_angle
    changing = (yaw_angle[1:] - yaw_angle[:-1])
    index_pos = (changing > 320)
    index_nega = (changing < -320)

    offset = 0

    # check the continuity of the adjacent yaw angle
    # if there is a sudden change of yaw angle, modify
    for i in range(1, len(yaw_angle) - 1):
        diff_yaw0 = yaw_angle0[i + 1] - yaw_angle[i]

        if index_pos[i]:
            offset = -360
            if abs(diff_yaw0) < 300:
                offset = 0

        elif index_nega[i]:
            offset = 360
            if abs(diff_yaw0) < 300:
                offset = 0

        else:
            pass

        yaw_angle[i + 1] = yaw_angle[i + 1] + offset
        diff = yaw_angle[i + 1] - yaw_angle[i]

        # check if it still needs compensation of 360 degree
        while abs(diff) > 300:
            if diff > 0:
                yaw_angle[i + 1] -= 360
            else:
                yaw_angle[i + 1] += 360

            diff = yaw_angle[i + 1] - yaw_angle[i]
    
    return yaw_angle
