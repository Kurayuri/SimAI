"""
This file can generate topology of AlibabaHPN, Spectrum-X, DCN+.
Users can freely customize the topology according to their needs。
"""

import argparse
import re
import warnings


def Rail_Opti_SingleToR(parameters):
    nodes_per_asw = parameters['nics_per_aswitch']
    asw_switch_num_per_segment = parameters['gpu_per_server']
    if (parameters['gpu'] % (nodes_per_asw * asw_switch_num_per_segment) == 0):
        segment_num = (int)(parameters['gpu'] / (nodes_per_asw * asw_switch_num_per_segment))
    else:
        segment_num = (int)(parameters['gpu'] / (nodes_per_asw * asw_switch_num_per_segment)) + 1

    if (segment_num != parameters['asw_switch_num'] / asw_switch_num_per_segment):
        warnings.warn("Error relations between total GPU Nums and total aws_switch_num.\n \
                         The correct asw_switch_num is set to " + str(segment_num * asw_switch_num_per_segment))
        parameters['asw_switch_num'] = segment_num * asw_switch_num_per_segment
    print("asw_switch_num: " + str(parameters['asw_switch_num']))
    if segment_num > int(parameters['asw_per_psw'] / asw_switch_num_per_segment):
        raise ValueError("Number of GPU exceeds the capacity of Rail_Optimized_SingleToR(One Pod)")
    pod_num = 1
    print("psw_switch_num: " + str(parameters['psw_switch_num']))
    print("Creating Topology of totally " + str(segment_num) + " segment(s), totally " + str(pod_num) + " pod(s).")

    nv_switch_num = (int)(parameters['gpu'] / parameters['gpu_per_server']) * parameters['nv_switch_per_server']
    nodes = (int)(parameters['gpu'] + parameters['asw_switch_num'] + parameters['psw_switch_num'] + nv_switch_num)
    servers = parameters['gpu'] / parameters['gpu_per_server']
    switch_nodes = (int)(parameters['psw_switch_num'] + parameters['asw_switch_num'] + nv_switch_num)
    links = (int)(parameters['psw_switch_num'] / pod_num * parameters['asw_switch_num'] + servers * asw_switch_num_per_segment
                  + servers * parameters['nv_switch_per_server'] * parameters['gpu_per_server'])
    if parameters['topology'] == 'Spectrum-X':
        file_name = "Spectrum-X_" + str(parameters['gpu']) + "g_" + str(parameters['gpu_per_server']) + \
            "gps_" + parameters['bandwidth'] + "_" + parameters['gpu_type']
    else:
        file_name = "Rail_Opti_SingleToR_" + \
            str(parameters['gpu']) + "g_" + str(parameters['gpu_per_server']) + \
            "gps_" + parameters['bandwidth'] + "_" + parameters['gpu_type']
    with open(file_name, 'w') as f:
        print(file_name)
        first_line = str(nodes) + " " + str(parameters['gpu_per_server']) + " " + str(nv_switch_num) + " " + \
            str(switch_nodes - nv_switch_num) + " " + str(int(links)) + " " + str(parameters['gpu_type'])
        f.write(first_line)
        f.write('\n')
        nv_switch = []
        asw_switch = []
        psw_switch = []
        dsw_switch = []
        sec_line = ""
        nnodes = nodes - switch_nodes
        for i in range(nnodes, nodes):
            sec_line = sec_line + str(i) + " "
            if len(nv_switch) < nv_switch_num:
                nv_switch.append(i)
            elif len(asw_switch) < parameters['asw_switch_num']:
                asw_switch.append(i)
            elif len(psw_switch) < parameters['psw_switch_num']:
                psw_switch.append(i)
            else:
                dsw_switch.append(i)
        f.write(sec_line)
        f.write('\n')
        ind_asw = 0
        curr_node = 0
        group_num = 0
        group_account = 0
        ind_nv = 0
        for i in range(parameters['gpu']):
            curr_node = curr_node + 1
            if curr_node > parameters['gpu_per_server']:
                curr_node = 1
                ind_nv = ind_nv + parameters['nv_switch_per_server']
            for j in range(0, parameters['nv_switch_per_server']):
                # cnt += 1
                line = str(i) + " " + str(nv_switch[ind_nv + j]) + " " + str(parameters['nvlink_bw']) + \
                    " " + str(parameters['nv_latency']) + " " + str(parameters['error_rate'])
                f.write(line)
                f.write('\n')
            line = str(i) + " " + str(asw_switch[group_num * asw_switch_num_per_segment + ind_asw]) + " " + \
                str(parameters['bandwidth']) + " " + str(parameters['latency']) + " " + str(parameters['error_rate'])
            f.write(line)
            f.write('\n')
            ind_asw = ind_asw + 1
            group_account = group_account + 1

            if ind_asw == asw_switch_num_per_segment:
                ind_asw = 0
            if group_account == (parameters['gpu_per_server'] * parameters['nics_per_aswitch']):
                group_num = group_num + 1
                group_account = 0

        for i in asw_switch:  # asw - psw
            for j in psw_switch:
                line = str(i) + " " + str(j) + " " + str(parameters['ap_bandwidth']) + \
                    " " + str(parameters['latency']) + " " + str(parameters['error_rate'])
                f.write(line)
                f.write('\n')


def Rail_Opti_DualToR_SinglePlane(parameters):
    nodes_per_asw = parameters['nics_per_aswitch']
    asw_switch_num_per_segment = parameters['gpu_per_server'] * 2
    if (parameters['gpu'] % (nodes_per_asw * asw_switch_num_per_segment / 2) == 0):
        segment_num = (int)(parameters['gpu'] / (nodes_per_asw * asw_switch_num_per_segment / 2))
    else:
        segment_num = (int)(parameters['gpu'] / (nodes_per_asw * asw_switch_num_per_segment / 2)) + 1

    if (segment_num != parameters['asw_switch_num'] / asw_switch_num_per_segment):
        warnings.warn("Error relations between total GPU Nums and total aws_switch_num.\n \
                         The correct asw_switch_num is set to " + str(segment_num * asw_switch_num_per_segment))
        parameters['asw_switch_num'] = segment_num * asw_switch_num_per_segment
    print("asw_switch_num: " + str(parameters['asw_switch_num']))
    if segment_num > int(parameters['asw_per_psw'] / (asw_switch_num_per_segment / 2)):
        raise ValueError("Number of GPU exceeds the capacity of Rail_Optimized_SingleToR(One Pod)")
    pod_num = 1
    print("psw_switch_num: " + str(parameters['psw_switch_num']))
    print("Creating Topology of totally " + str(segment_num) + " segment(s), totally " + str(pod_num) + " pod(s).")

    nv_switch_num = (int)(parameters['gpu'] / parameters['gpu_per_server']) * parameters['nv_switch_per_server']
    nodes = (int)(parameters['gpu'] + parameters['asw_switch_num'] + parameters['psw_switch_num'] + nv_switch_num)
    servers = parameters['gpu'] / parameters['gpu_per_server']
    switch_nodes = (int)(parameters['psw_switch_num'] + parameters['asw_switch_num'] + nv_switch_num)
    links = (int)(parameters['psw_switch_num'] / pod_num * parameters['asw_switch_num'] + servers * asw_switch_num_per_segment
                  + servers * parameters['nv_switch_per_server'] * parameters['gpu_per_server'])
    if parameters['topology'] == 'AlibabaHPN':
        file_name = "AlibabaHPN_" + str(parameters['gpu']) + "g_" + str(parameters['gpu_per_server']) + \
            "gps_DualToR_SinglePlane_" + parameters['bandwidth'] + "_" + parameters['gpu_type']
    else:
        file_name = "Rail_Opti_" + str(parameters['gpu']) + "g_" + str(parameters['gpu_per_server']) + \
            "gps_DualToR_SinglePlane_" + parameters['bandwidth'] + "_" + parameters['gpu_type']
    with open(file_name, 'w') as f:
        print(file_name)
        first_line = str(nodes) + " " + str(parameters['gpu_per_server']) + " " + str(nv_switch_num) + " " + \
            str(switch_nodes - nv_switch_num) + " " + str(int(links)) + " " + str(parameters['gpu_type'])
        f.write(first_line)
        f.write('\n')
        nv_switch = []
        asw_switch_1 = []
        asw_switch_2 = []
        psw_switch = []
        dsw_switch = []
        sec_line = ""
        nnodes = nodes - switch_nodes
        for i in range(nnodes, nodes):
            sec_line = sec_line + str(i) + " "
            if len(nv_switch) < nv_switch_num:
                nv_switch.append(i)
            elif len(asw_switch_1) < parameters['asw_switch_num'] / 2:
                asw_switch_1.append(i)
            elif len(asw_switch_2) < parameters['asw_switch_num'] / 2:
                asw_switch_2.append(i)
            elif len(psw_switch) < parameters['psw_switch_num']:
                psw_switch.append(i)
            else:
                dsw_switch.append(i)
        f.write(sec_line)
        f.write('\n')
        ind_asw = 0
        curr_node = 0
        group_num = 0
        group_account = 0
        ind_nv = 0
        for i in range(parameters['gpu']):
            curr_node = curr_node + 1
            if curr_node > parameters['gpu_per_server']:
                curr_node = 1
                ind_nv = ind_nv + parameters['nv_switch_per_server']
            for j in range(0, parameters['nv_switch_per_server']):
                # cnt += 1
                line = str(i) + " " + str(nv_switch[ind_nv + j]) + " " + str(parameters['nvlink_bw']) + \
                    " " + str(parameters['nv_latency']) + " " + str(parameters['error_rate'])
                f.write(line)
                f.write('\n')
            line = str(i) + " " + str(asw_switch_1[group_num * int(asw_switch_num_per_segment / 2) + ind_asw]) + " " + \
                str(parameters['bandwidth']) + " " + str(parameters['latency']) + " " + str(parameters['error_rate'])
            f.write(line)
            f.write('\n')

            line = str(i) + " " + str(asw_switch_2[group_num * int(asw_switch_num_per_segment / 2) + ind_asw]) + " " + \
                str(parameters['bandwidth']) + " " + str(parameters['latency']) + " " + str(parameters['error_rate'])
            f.write(line)
            f.write('\n')

            ind_asw = ind_asw + 1
            group_account = group_account + 1

            if ind_asw == int(asw_switch_num_per_segment / 2):
                ind_asw = 0
            if group_account == (parameters['gpu_per_server'] * parameters['nics_per_aswitch']):
                group_num = group_num + 1
                group_account = 0

        for i in asw_switch_1:  # asw - psw
            for j in psw_switch:
                line = str(i) + " " + str(j) + " " + str(parameters['ap_bandwidth']) + \
                    " " + str(parameters['latency']) + " " + str(parameters['error_rate'])
                f.write(line)
                f.write('\n')
        for i in asw_switch_2:  # asw - psw
            for j in psw_switch:
                line = str(i) + " " + str(j) + " " + str(parameters['ap_bandwidth']) + \
                    " " + str(parameters['latency']) + " " + str(parameters['error_rate'])
                f.write(line)
                f.write('\n')


def Rail_Opti_DualToR_DualPlane(parameters):
    nodes_per_asw = parameters['nics_per_aswitch']
    asw_switch_num_per_segment = parameters['gpu_per_server'] * 2
    if (parameters['gpu'] % (nodes_per_asw * asw_switch_num_per_segment / 2) == 0):
        segment_num = (int)(parameters['gpu'] / (nodes_per_asw * asw_switch_num_per_segment / 2))
    else:
        segment_num = (int)(parameters['gpu'] / (nodes_per_asw * asw_switch_num_per_segment / 2)) + 1

    if (segment_num != parameters['asw_switch_num'] / asw_switch_num_per_segment):
        warnings.warn("Error relations between total GPU Nums and total aws_switch_num.\n \
                         The correct asw_switch_num is set to " + str(segment_num * asw_switch_num_per_segment))
        parameters['asw_switch_num'] = segment_num * asw_switch_num_per_segment
    print("asw_switch_num: " + str(parameters['asw_switch_num']))
    if segment_num > int(parameters['asw_per_psw'] / (asw_switch_num_per_segment / 2)):
        raise ValueError("Number of GPU exceeds the capacity of Rail_Optimized_SingleToR(One Pod)")
    pod_num = 1
    print("psw_switch_num: " + str(parameters['psw_switch_num']))
    print("Creating Topology of totally " + str(segment_num) + " segment(s), totally " + str(pod_num) + " pod(s).")

    nv_switch_num = (int)(parameters['gpu'] / parameters['gpu_per_server']) * parameters['nv_switch_per_server']
    nodes = (int)(parameters['gpu'] + parameters['asw_switch_num'] + parameters['psw_switch_num'] + nv_switch_num)
    servers = parameters['gpu'] / parameters['gpu_per_server']
    switch_nodes = (int)(parameters['psw_switch_num'] + parameters['asw_switch_num'] + nv_switch_num)
    links = (int)(parameters['psw_switch_num'] / pod_num / 2 * parameters['asw_switch_num'] + servers * asw_switch_num_per_segment
                  + servers * parameters['nv_switch_per_server'] * parameters['gpu_per_server'])
    if parameters['topology'] == 'AlibabaHPN':
        file_name = "AlibabaHPN_" + str(parameters['gpu']) + "g_" + str(parameters['gpu_per_server']) + \
            "gps_DualToR_DualPlane_" + parameters['bandwidth'] + "_" + parameters['gpu_type']
    else:
        file_name = "Rail_Opti_" + str(parameters['gpu']) + "g_" + str(parameters['gpu_per_server']) + \
            "gps_DualToR_DualPlane_" + parameters['bandwidth'] + "_" + parameters['gpu_type']
    with open(file_name, 'w') as f:
        print(file_name)
        first_line = str(nodes) + " " + str(parameters['gpu_per_server']) + " " + str(nv_switch_num) + " " + \
            str(switch_nodes - nv_switch_num) + " " + str(int(links)) + " " + str(parameters['gpu_type'])
        f.write(first_line)
        f.write('\n')
        nv_switch = []
        asw_switch_1 = []
        asw_switch_2 = []
        psw_switch_1 = []
        psw_switch_2 = []
        dsw_switch = []
        sec_line = ""
        nnodes = nodes - switch_nodes
        for i in range(nnodes, nodes):
            sec_line = sec_line + str(i) + " "
            if len(nv_switch) < nv_switch_num:
                nv_switch.append(i)
            elif len(asw_switch_1) < parameters['asw_switch_num'] / 2:
                asw_switch_1.append(i)
            elif len(asw_switch_2) < parameters['asw_switch_num'] / 2:
                asw_switch_2.append(i)
            elif len(psw_switch_1) < parameters['psw_switch_num'] / 2:
                psw_switch_1.append(i)
            elif len(psw_switch_2) < parameters['psw_switch_num'] / 2:
                psw_switch_2.append(i)
            else:
                dsw_switch.append(i)
        f.write(sec_line)
        f.write('\n')
        ind_asw = 0
        curr_node = 0
        group_num = 0
        group_account = 0
        ind_nv = 0
        for i in range(parameters['gpu']):
            curr_node = curr_node + 1
            if curr_node > parameters['gpu_per_server']:
                curr_node = 1
                ind_nv = ind_nv + parameters['nv_switch_per_server']
            for j in range(0, parameters['nv_switch_per_server']):
                # cnt += 1
                line = str(i) + " " + str(nv_switch[ind_nv + j]) + " " + str(parameters['nvlink_bw']) + \
                    " " + str(parameters['nv_latency']) + " " + str(parameters['error_rate'])
                f.write(line)
                f.write('\n')
            line = str(i) + " " + str(asw_switch_1[group_num * int(asw_switch_num_per_segment / 2) + ind_asw]) + " " + \
                str(parameters['bandwidth']) + " " + str(parameters['latency']) + " " + str(parameters['error_rate'])
            f.write(line)
            f.write('\n')

            line = str(i) + " " + str(asw_switch_2[group_num * int(asw_switch_num_per_segment / 2) + ind_asw]) + " " + \
                str(parameters['bandwidth']) + " " + str(parameters['latency']) + " " + str(parameters['error_rate'])
            f.write(line)
            f.write('\n')

            ind_asw = ind_asw + 1
            group_account = group_account + 1

            if ind_asw == int(asw_switch_num_per_segment / 2):
                ind_asw = 0
            if group_account == (parameters['gpu_per_server'] * parameters['nics_per_aswitch']):
                group_num = group_num + 1
                group_account = 0

        for i in asw_switch_1:  # asw - psw
            for j in psw_switch_1:
                line = str(i) + " " + str(j) + " " + str(parameters['ap_bandwidth']) + \
                    " " + str(parameters['latency']) + " " + str(parameters['error_rate'])
                f.write(line)
                f.write('\n')
        for i in asw_switch_2:  # asw - psw
            for j in psw_switch_2:
                line = str(i) + " " + str(j) + " " + str(parameters['ap_bandwidth']) + \
                    " " + str(parameters['latency']) + " " + str(parameters['error_rate'])
                f.write(line)
                f.write('\n')


def No_Rail_Opti_SingleToR(parameters):
    nodes_per_asw = parameters['nics_per_aswitch']
    asw_switch_num_per_segment = 1
    if (parameters['gpu'] % (nodes_per_asw * asw_switch_num_per_segment) == 0):
        segment_num = (int)(parameters['gpu'] / (nodes_per_asw * asw_switch_num_per_segment))
    else:
        segment_num = (int)(parameters['gpu'] / (nodes_per_asw * asw_switch_num_per_segment)) + 1

    if (segment_num != parameters['asw_switch_num'] / asw_switch_num_per_segment):
        warnings.warn("Error relations between total GPU Nums and total aws_switch_num.\n \
                         The correct asw_switch_num is set to " + str(segment_num * asw_switch_num_per_segment))
        parameters['asw_switch_num'] = segment_num * asw_switch_num_per_segment
    print("asw_switch_num: " + str(parameters['asw_switch_num']))
    if segment_num > int(parameters['asw_per_psw'] / asw_switch_num_per_segment):
        raise ValueError("Number of GPU exceeds the capacity of Rail_Optimized_SingleToR(One Pod)")
    pod_num = 1
    print("psw_switch_num: " + str(parameters['psw_switch_num']))
    print("Creating Topology of totally " + str(segment_num) + " segment(s), totally " + str(pod_num) + " pod(s).")

    nv_switch_num = (int)(parameters['gpu'] / parameters['gpu_per_server']) * parameters['nv_switch_per_server']
    nodes = (int)(parameters['gpu'] + parameters['asw_switch_num'] + parameters['psw_switch_num'] + nv_switch_num)
    servers = parameters['gpu'] / parameters['gpu_per_server']
    switch_nodes = (int)(parameters['psw_switch_num'] + parameters['asw_switch_num'] + nv_switch_num)
    links = (int)(parameters['psw_switch_num'] / pod_num * parameters['asw_switch_num'] + servers * parameters['gpu_per_server']
                  + servers * parameters['nv_switch_per_server'] * parameters['gpu_per_server'])
    if parameters['topology'] == 'DCN+':
        file_name = "DCN+SingleToR_" + str(parameters['gpu']) + "g_" + str(parameters['gpu_per_server']) + \
            "gps_" + parameters['bandwidth'] + "_" + parameters['gpu_type']
    else:
        file_name = "No_Rail_Opti_" + str(parameters['gpu']) + "g_" + str(parameters['gpu_per_server']) + \
            "gps_SingleToR_" + parameters['bandwidth'] + "_" + parameters['gpu_type']
    with open(file_name, 'w') as f:
        print(file_name)
        first_line = str(nodes) + " " + str(parameters['gpu_per_server']) + " " + str(nv_switch_num) + " " + \
            str(switch_nodes - nv_switch_num) + " " + str(int(links)) + " " + str(parameters['gpu_type'])
        f.write(first_line)
        f.write('\n')
        nv_switch = []
        asw_switch = []
        psw_switch = []
        dsw_switch = []
        sec_line = ""
        nnodes = nodes - switch_nodes
        for i in range(nnodes, nodes):
            sec_line = sec_line + str(i) + " "
            if len(nv_switch) < nv_switch_num:
                nv_switch.append(i)
            elif len(asw_switch) < parameters['asw_switch_num']:
                asw_switch.append(i)
            elif len(psw_switch) < parameters['psw_switch_num']:
                psw_switch.append(i)
            else:
                dsw_switch.append(i)
        f.write(sec_line)
        f.write('\n')
        ind_asw = 0
        curr_node = 0
        group_num = 0
        group_account = 0
        ind_nv = 0
        for i in range(parameters['gpu']):
            curr_node = curr_node + 1
            if curr_node > parameters['gpu_per_server']:
                curr_node = 1
                ind_nv = ind_nv + parameters['nv_switch_per_server']
            for j in range(0, parameters['nv_switch_per_server']):
                # cnt += 1
                line = str(i) + " " + str(nv_switch[ind_nv + j]) + " " + str(parameters['nvlink_bw']) + \
                    " " + str(parameters['nv_latency']) + " " + str(parameters['error_rate'])
                f.write(line)
                f.write('\n')
            line = str(i) + " " + str(asw_switch[group_num * asw_switch_num_per_segment + ind_asw]) + " " + \
                str(parameters['bandwidth']) + " " + str(parameters['latency']) + " " + str(parameters['error_rate'])
            f.write(line)
            f.write('\n')
            group_account = group_account + 1

            if group_account == nodes_per_asw:
                group_num = group_num + 1
                group_account = 0

        for i in asw_switch:  # asw - psw
            for j in psw_switch:
                line = str(i) + " " + str(j) + " " + str(parameters['ap_bandwidth']) + \
                    " " + str(parameters['latency']) + " " + str(parameters['error_rate'])
                f.write(line)
                f.write('\n')


def No_Rail_Opti_DualToR(parameters):
    nodes_per_asw = parameters['nics_per_aswitch']
    asw_switch_num_per_segment = 2
    if (parameters['gpu'] % (nodes_per_asw * (asw_switch_num_per_segment / 2)) == 0):
        segment_num = (int)(parameters['gpu'] / (nodes_per_asw * asw_switch_num_per_segment / 2))
    else:
        segment_num = (int)(parameters['gpu'] / (nodes_per_asw * asw_switch_num_per_segment / 2)) + 1
    if (segment_num != parameters['asw_switch_num'] / asw_switch_num_per_segment):
        warnings.warn("Error relations between total GPU Nums and total aws_switch_num.\n \
                         The correct asw_switch_num is set to " + str(segment_num * asw_switch_num_per_segment))
        parameters['asw_switch_num'] = segment_num * asw_switch_num_per_segment
    print("asw_switch_num: " + str(parameters['asw_switch_num']))
    if segment_num > int(parameters['asw_per_psw'] / asw_switch_num_per_segment):
        raise ValueError("Number of GPU exceeds the capacity of Rail_Optimized_SingleToR(One Pod)")
    pod_num = 1
    print("psw_switch_num: " + str(parameters['psw_switch_num']))
    print("Creating Topology of totally " + str(segment_num) + " segment(s), totally " + str(pod_num) + " pod(s).")

    nv_switch_num = (int)(parameters['gpu'] / parameters['gpu_per_server']) * parameters['nv_switch_per_server']
    nodes = (int)(parameters['gpu'] + parameters['asw_switch_num'] + parameters['psw_switch_num'] + nv_switch_num)
    servers = parameters['gpu'] / parameters['gpu_per_server']
    switch_nodes = (int)(parameters['psw_switch_num'] + parameters['asw_switch_num'] + nv_switch_num)
    links = (int)(parameters['psw_switch_num'] / pod_num * parameters['asw_switch_num'] + servers * parameters['gpu_per_server'] * 2
                  + servers * parameters['nv_switch_per_server'] * parameters['gpu_per_server'])
    if parameters['topology'] == 'DCN+':
        file_name = "DCN+DualToR_" + str(parameters['gpu']) + "g_" + str(parameters['gpu_per_server']) + \
            "gps_" + parameters['bandwidth'] + "_" + parameters['gpu_type']
    else:
        file_name = "No_Rail_Opti_" + str(parameters['gpu']) + "g_" + str(parameters['gpu_per_server']) + \
            "gps_DualToR_" + parameters['bandwidth'] + "_" + parameters['gpu_type']
    with open(file_name, 'w') as f:
        print(file_name)
        first_line = str(nodes) + " " + str(parameters['gpu_per_server']) + " " + str(nv_switch_num) + " " + \
            str(switch_nodes - nv_switch_num) + " " + str(int(links)) + " " + str(parameters['gpu_type'])
        f.write(first_line)
        f.write('\n')
        nv_switch = []
        asw_switch_1 = []
        asw_switch_2 = []
        psw_switch = []
        dsw_switch = []
        sec_line = ""
        nnodes = nodes - switch_nodes
        for i in range(nnodes, nodes):
            sec_line = sec_line + str(i) + " "
            if len(nv_switch) < nv_switch_num:
                nv_switch.append(i)
            elif len(asw_switch_1) < parameters['asw_switch_num'] / 2:
                asw_switch_1.append(i)
            elif len(asw_switch_2) < parameters['asw_switch_num'] / 2:
                asw_switch_2.append(i)
            elif len(psw_switch) < parameters['psw_switch_num']:
                psw_switch.append(i)
            else:
                dsw_switch.append(i)
        f.write(sec_line)
        f.write('\n')
        ind_asw = 0
        curr_node = 0
        group_num = 0
        group_account = 0
        ind_nv = 0
        for i in range(parameters['gpu']):
            curr_node = curr_node + 1
            if curr_node > parameters['gpu_per_server']:
                curr_node = 1
                ind_nv = ind_nv + parameters['nv_switch_per_server']
            for j in range(0, parameters['nv_switch_per_server']):
                # cnt += 1
                line = str(i) + " " + str(nv_switch[ind_nv + j]) + " " + str(parameters['nvlink_bw']) + \
                    " " + str(parameters['nv_latency']) + " " + str(parameters['error_rate'])
                f.write(line)
                f.write('\n')
            line = str(i) + " " + str(asw_switch_1[group_num * int(asw_switch_num_per_segment / 2) + ind_asw]) + " " + \
                str(parameters['bandwidth']) + " " + str(parameters['latency']) + " " + str(parameters['error_rate'])
            f.write(line)
            f.write('\n')

            line = str(i) + " " + str(asw_switch_2[group_num * int(asw_switch_num_per_segment / 2) + ind_asw]) + " " + \
                str(parameters['bandwidth']) + " " + str(parameters['latency']) + " " + str(parameters['error_rate'])
            f.write(line)
            f.write('\n')
            group_account = group_account + 1

            if group_account == nodes_per_asw:
                group_num = group_num + 1
                group_account = 0

        for i in asw_switch_1:  # asw - psw
            for j in psw_switch:
                line = str(i) + " " + str(j) + " " + str(parameters['ap_bandwidth']) + \
                    " " + str(parameters['latency']) + " " + str(parameters['error_rate'])
                f.write(line)
                f.write('\n')
        for i in asw_switch_2:  # asw - psw
            for j in psw_switch:
                line = str(i) + " " + str(j) + " " + str(parameters['ap_bandwidth']) + \
                    " " + str(parameters['latency']) + " " + str(parameters['error_rate'])
                f.write(line)
                f.write('\n')


def write_link(f, src_id, dst_id, bw, latency, error_rate):
    line = f"{src_id} {dst_id} {bw} {latency} {error_rate}\n"
    f.write(line)


def proc_volume(vol, fn=None):
    pattern = re.compile(r"(\d+(\.\d+)?)([a-zA-Z]*)")
    match = pattern.match(vol).groups()
    num = match[0]
    dot = match[1]
    unit = match[2]
    num = float(num) if dot else int(num)

    if fn:
        num = fn(num)
        return f"{num}{unit}"
    else:
        return num, unit


def NVL(parameters):
    gpu_per_rack = parameters['gpu_per_server']
    gpu_per_server = gpu_per_rack
    assert gpu_per_rack in [36, 72], "gpu_per_rack/server should be 36 or 72"
    nv_switch_per_rack = parameters['nv_switch_per_server']
    nv_switch_per_server = nv_switch_per_rack

    nics_per_nv_switch = parameters['nics_per_nv_switch']
    assert nics_per_nv_switch in [72], "nics_per_aswitch should be 72"

    assert nv_switch_per_rack in [18], "nv_switch_per_rack/server should be 18"
    nv_rack_switch_per_plane_switch = parameters['nv_rack_switch_per_plane_switch']
    n_nv_plane_switches_per_nv_pod = parameters['nv_plane_switch_per_nv_pod']
    n_nv_plane_switches = parameters['nv_plane_switch_num']

    assert n_nv_plane_switches % n_nv_plane_switches_per_nv_pod == 0
    n_nv_pods = n_nv_plane_switches // n_nv_plane_switches_per_nv_pod

    nvl_type = f"{gpu_per_rack}" if n_nv_pods == 0 else f"576"
    nvlink_bw = parameters['nvlink_bw']
    nvlink_latency = parameters['nv_latency']
    error_rate = parameters['error_rate']
    n_gpus = parameters['gpu']
    n_racks = int(n_gpus / gpu_per_rack)

    print("asw_switch_num: " + str(parameters['asw_switch_num']))
    print("psw_switch_num: " + str(parameters['psw_switch_num']))
    segment_num = 1
    pod_num = 1

    print("Creating Topology of totally " + str(segment_num) + " segment(s), totally " + str(pod_num) + " pod(s).")

    file_name = "NVL" + str(nvl_type) + "_" + str(n_gpus) + "g_" + str(gpu_per_rack) + \
        "gps_" + parameters['bandwidth'] + "_" + parameters['gpu_type']

    # nodes_per_asw = parameters['nics_per_aswitch']
    # asw_switch_num_per_segment = parameters['gpu_per_server']
    # if (parameters['gpu'] % (nodes_per_asw * asw_switch_num_per_segment) == 0):
    #     segment_num = (int)(parameters['gpu'] / (nodes_per_asw * asw_switch_num_per_segment))
    # else:
    #     segment_num = (int)(parameters['gpu'] / (nodes_per_asw * asw_switch_num_per_segment)) + 1

    # if (segment_num != parameters['asw_switch_num'] / asw_switch_num_per_segment):
    #     warnings.warn("Error relations between total GPU Nums and total aws_switch_num.\n \
    #                      The correct asw_switch_num is set to " + str(segment_num * asw_switch_num_per_segment))
    #     parameters['asw_switch_num'] = segment_num * asw_switch_num_per_segment
    # print("asw_switch_num: " + str(parameters['asw_switch_num']))
    # if segment_num > int(parameters['asw_per_psw'] / asw_switch_num_per_segment):
    #     raise ValueError("Number of GPU exceeds the capacity of Rail_Optimized_SingleToR(One Pod)")
    # pod_num = 1
    # print("psw_switch_num: " + str(parameters['psw_switch_num']))
    # print("Creating Topology of totally " + str(segment_num) + " segment(s), totally " + str(pod_num) + " pod(s).")
    left_nics_per_nv_rack_switch = nics_per_nv_switch - gpu_per_rack
    if n_nv_pods > 0:
        assert left_nics_per_nv_rack_switch > 0
        n_rack_switches_per_nv_pod = n_nv_plane_switches_per_nv_pod * nv_rack_switch_per_plane_switch // left_nics_per_nv_rack_switch
        n_racks_per_nv_pod = n_rack_switches_per_nv_pod // nv_switch_per_rack

    n_nv_rack_switches = n_racks * nv_switch_per_rack
    n_nv_plane_switches = n_nv_plane_switches
    n_nv_switches = n_nv_rack_switches + n_nv_plane_switches

    n_servers = n_racks
    n_switches = n_nv_switches + parameters['asw_switch_num'] + parameters['psw_switch_num']
    n_nodes = n_gpus + n_switches

    n_nv_plane_rack_switch_links = n_nv_plane_switches * nv_rack_switch_per_plane_switch
    n_nv_gpu_rack_switch_links = n_gpus * nv_switch_per_rack

    n_nv_rack_rack_switch_links = 0
    if n_nv_pods == 0:
        n_nv_rack_rack_switch_links = (n_racks) * (n_racks - 1) / 2 * nv_switch_per_rack

    n_nv_links = n_nv_gpu_rack_switch_links + n_nv_plane_rack_switch_links + n_nv_rack_rack_switch_links  # TODO

    n_links = n_nv_links

    with open(file_name, 'w') as f:
        print(file_name)
        first_line = str(n_nodes) + " " + str(parameters['gpu_per_server']) + " " + str(n_nv_switches) + " " + \
            str(n_switches - n_nv_switches) + " " + str(int(n_links)) + " " + str(parameters['gpu_type'])
        f.write(first_line)
        f.write('\n')

        nv_switches = []  # rack_nv_switches
        asw_switch = []
        psw_switch = []
        dsw_switch = []
        sec_line = ""
        nnodes = n_nodes - n_switches
        for nv_pod_idx in range(nnodes, n_nodes):
            sec_line = sec_line + str(nv_pod_idx) + " "
            if len(nv_switches) < n_nv_switches:
                nv_switches.append(nv_pod_idx)
            elif len(asw_switch) < parameters['asw_switch_num']:
                asw_switch.append(nv_pod_idx)
            elif len(psw_switch) < parameters['psw_switch_num']:
                psw_switch.append(nv_pod_idx)
            else:
                dsw_switch.append(nv_pod_idx)
        f.write(sec_line)
        f.write('\n')
        ind_asw = 0
        curr_node = 0
        group_num = 0
        group_account = 0
        ind_nv = 0
        for nv_pod_idx in range(n_gpus):
            curr_node = curr_node + 1
            if curr_node > gpu_per_server:
                curr_node = 1
                ind_nv = ind_nv + nv_switch_per_rack
            for nv_plane_idx in range(0, nv_switch_per_server):
                # cnt += 1
                line = str(nv_pod_idx) + " " + str(nv_switches[ind_nv + nv_plane_idx]) + " " + str(parameters['nvlink_bw']) + \
                    " " + str(parameters['nv_latency']) + " " + str(parameters['error_rate'])
                f.write(line)
                f.write('\n')
            # line = str(i) + " " + str(asw_switch[group_num * asw_switch_num_per_segment + ind_asw]) + " " + \
            #     str(parameters['bandwidth']) + " " + str(parameters['latency']) + " " + str(parameters['error_rate'])
            # f.write(line)
            # f.write('\n')

            ind_asw = ind_asw + 1
            group_account = group_account + 1

        #     if ind_asw == asw_switch_num_per_segment:
        #         ind_asw = 0
        #     if group_account == (parameters['gpu_per_server'] * parameters['nics_per_aswitch']):
        #         group_num = group_num + 1
        #         group_account = 0

        # for i in asw_switch:  # asw - psw
        #     for j in psw_switch:
        #         line = str(i) + " " + str(j) + " " + str(parameters['ap_bandwidth']) + \
        #             " " + str(parameters['latency']) + " " + str(parameters['error_rate'])
        #         f.write(line)
        #         f.write('\n')

        if n_nv_pods == 0:
            if n_racks > 1:
                fused_nvlinks = left_nics_per_nv_rack_switch // (n_racks)
                fused_nvlink_bw = proc_volume(nvlink_bw, lambda n: n * fused_nvlinks)
                for nv_pod_idx in range(n_racks):
                    for nv_plane_idx in range(nv_pod_idx + 1, n_racks):
                        for k in range(nv_switch_per_rack):
                            src_id = nv_switches[nv_pod_idx * nv_switch_per_rack + k]
                            dst_id = nv_switches[nv_plane_idx * nv_switch_per_rack + k]
                            write_link(f, src_id, dst_id, fused_nvlink_bw, nvlink_latency, error_rate)
        else:
            nv_plane_switches = nv_switches[n_nv_rack_switches:]
            n_planes_per_pod = nv_switch_per_server // 2
            n_nv_plane_switches_per_plane = n_nv_plane_switches_per_nv_pod // n_planes_per_pod

            for nv_pod_idx in range(n_nv_pods):
                pod_plane_switch_offset = nv_pod_idx * n_nv_plane_switches_per_nv_pod
                pod_rack_switch_offset = nv_pod_idx * n_rack_switches_per_nv_pod

                for rack_idx in range(n_racks_per_nv_pod):
                    for rack_switch_idx in range(nv_switch_per_rack):
                        plane_idx = rack_switch_idx // 2
                        rack_switch_offset = pod_rack_switch_offset + rack_idx * nv_switch_per_rack + rack_switch_idx
                        plane_switch_offset = pod_plane_switch_offset + plane_idx * n_nv_plane_switches_per_plane
                        for plane_switch_idx in range(n_nv_plane_switches_per_plane):
                            plane_switch = nv_plane_switches[plane_switch_offset + plane_switch_idx]
                            rack_switch = nv_switches[rack_switch_offset]
                            write_link(f, rack_switch, plane_switch, nvlink_bw, nvlink_latency, error_rate)


def main():
    parser = argparse.ArgumentParser(description='Python script for generating a topology for SimAI')

    # Whole Structure Parameters:
    parser.add_argument('-topo', '--topology', type=str, default=None, help='Template for AlibabaHPN, Spectrum-X, DCN+')
    parser.add_argument('--ro', action='store_true', help='use rail-optimized structure')
    parser.add_argument('--dt', action='store_true', help='enable dual ToR, only for DCN+')
    parser.add_argument('--dp', action='store_true', help='enable dual_plane, only for AlibabaHPN')
    parser.add_argument('-g', '--gpu', type=int, default=None, help='gpus num, default 32')
    parser.add_argument('-er', '--error_rate', type=str, default=None, help='error_rate, default 0')
    # Intra-Host Parameters:
    parser.add_argument('-gps', '--gpu_per_server', type=int, default=None, help='gpu_per_server, default 8')
    parser.add_argument('-gt', '--gpu_type', type=str, default=None, help='gpu_type, default H100')
    parser.add_argument('-nsps', '--nv_switch_per_server', type=int, default=None, help='nv_switch_per_server, default 1')
    parser.add_argument('-nvbw', '--nvlink_bw', type=str, default=None, help='nvlink_bw, default 2880Gbps')
    parser.add_argument('-nl', '--nv_latency', type=str, default=None, help='nv switch latency, default 0.000025ms')
    parser.add_argument('-l', '--latency', type=str, default=None, help='nic latency, default 0.0005ms')
    # Intra-Segment Parameters:
    parser.add_argument('-bw', '--bandwidth', type=str, default=None, help='nic to asw bandwidth, default 400Gbps')
    parser.add_argument('-asn', '--asw_switch_num', type=int, default=None, help='asw_switch_num, default 8')
    parser.add_argument('-npa', '--nics_per_aswitch', type=int, default=None, help='nnics per asw, default 64')
    # Intra-Pod Parameters:
    parser.add_argument('-psn', '--psw_switch_num', type=int, default=None, help='psw_switch_num, default 64')
    parser.add_argument('-apbw', '--ap_bandwidth', type=str, default=None, help='asw to psw bandwidth,default 400Gbps')
    parser.add_argument('-app', '--asw_per_psw', type=int, default=None, help='asw for psw')
    args = parser.parse_args()

    default_parameters = []
    parameters = analysis_template(args, default_parameters)
    if parameters['topology'].startswith('NVL'):
        NVL(parameters)
    elif not parameters['rail_optimized']:
        if parameters['dual_plane']:
            raise ValueError("Sorry, None Rail-Optimized Structure doesn't support Dual Plane")
        if parameters['dual_ToR']:
            No_Rail_Opti_DualToR(parameters)
        else:
            No_Rail_Opti_SingleToR(parameters)
    else:
        if parameters['dual_ToR']:
            if parameters['dual_plane']:
                Rail_Opti_DualToR_DualPlane(parameters)
            else:
                Rail_Opti_DualToR_SinglePlane(parameters)
        else:
            if parameters['dual_plane']:
                raise ValueError("Sorry, Rail-optimized Single-ToR Structure doesn't support Dual Plane")
            Rail_Opti_SingleToR(parameters)


def analysis_template(args, default_parameters):
    # Basic default parameters
    default_parameters = {'rail_optimized': True, 'dual_ToR': False, 'dual_plane': False, 'gpu': 32, 'error_rate': 0,
                          'gpu_per_server': 8, 'gpu_type': 'H100', 'nv_switch_per_server': 1,
                          'nvlink_bw': '2880Gbps', 'nv_latency': '0.000025ms', 'latency': '0.0005ms',
                          'bandwidth': '400Gbps', 'asw_switch_num': 8, 'nics_per_aswitch': 64,
                          'psw_switch_num': 64, 'ap_bandwidth': "400Gbps", 'asw_per_psw': 64}
    parameters = {}
    parameters['topology'] = args.topology
    parameters['rail_optimized'] = bool(args.ro)
    parameters['dual_ToR'] = bool(args.dt)
    parameters['dual_plane'] = bool(args.dp)

    if parameters['topology'] == 'Spectrum-X':
        default_parameters.update({
            'gpu': 4096
        })
        parameters.update({
            'rail_optimized': True,
            'dual_ToR': False,
            'dual_plane': False,
        })
    elif parameters['topology'] == 'AlibabaHPN':
        default_parameters.update({
            'gpu': 15360,
            'bandwidth': '200Gbps',
            'asw_switch_num': 240,
            'nics_per_aswitch': 128,
            'psw_switch_num': 120,
            'asw_per_psw': 240
        })
        parameters.update({
            'rail_optimized': True,
            'dual_ToR': True,
            'dual_plane': False,

        })
        if args.dp:
            default_parameters.update({
                'asw_per_psw': 120
            })
            parameters.update({
                'rail_optimized': True,
                'dual_ToR': True,
                'dual_plane': True,
            })
    elif parameters['topology'] == 'DCN+':
        default_parameters.update({
            'gpu': 512,
            'asw_switch_num': 8,
            'asw_per_psw': 8,
            'psw_switch_num': 8
        })
        parameters.update({
            'rail_optimized': False,
            'dual_ToR': False,
            'dual_plane': False,
        })
        if args.dt:
            default_parameters.update({
                'bandwidth': '200Gbps',
                'nics_per_aswitch': 128,
            })
            parameters.update({
                'rail_optimized': False,
                'dual_ToR': True,
                'dual_plane': False,
            })
    elif parameters['topology'].startswith('NVL'):
        default_parameters.update({
            "gpu": 72,
            "gpu_per_server": 72,  # 36/72
            # "gpu_per_rack": 36 / 72,
            "nv_rack_switch_per_plane_switch": 32,
            "gpu_type": "B200",
            "nv_switch_per_server": 18,
            "nv_plane_switch_per_nv_pod": 324,
            "nv_plane_switch_num": 0,

            # "nv_switch_per_rack": 18,
            "nvlink_bw": "800Gbps",
            "nv_latency": "0.000025ms",
            "latency": "0.0005ms",
            "bandwidth": "400Gbps",
            "asw_switch_num": 0,
            "nics_per_aswitch": 0,
            "nics_per_nv_switch": 72,
            "psw_switch_num": 0,
            "ap_bandwidth": "400Gbps",
            # "asw_per_psw": 0,
        })
        if parameters['topology'].endswith('36'):
            default_parameters['gpu_per_server'] = 36

        elif parameters['topology'].endswith('576'):
            default_parameters['gpu'] = 576
            default_parameters['gpu_per_server'] = 36
            default_parameters['nv_plane_switch_num'] = 324

    parameter_keys = [
        'gpu', 'error_rate', 'gpu_per_server', 'gpu_type', 'nv_switch_per_server',
        'nvlink_bw', 'nv_latency', 'latency', 'bandwidth', 'asw_switch_num',
        'nics_per_aswitch', 'psw_switch_num', 'ap_bandwidth', 'asw_per_psw',
        'nv_switch_per_server', 'nics_per_nv_switch', "nv_rack_switch_per_plane_switch", "nv_plane_switch_per_nv_pod", "nv_plane_switch_num"  # NVL
    ]

    for key in parameter_keys:
        parameters[key] = getattr(args, key, None) if getattr(args, key, None) is not None else default_parameters[key]
    # for key, value in parameters.items():
    #     print(f'{key}: {value}')
    # print("==================================")
    return parameters


if __name__ == '__main__':
    main()
