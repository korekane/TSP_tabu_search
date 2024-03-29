# -*- coding: utf-8 -*-
"""
Created on Wed Nov 17 19:07:48 2021
@author: korekane1998
tabu-search for TSP
"""
import math
import random
import time
import gurobipy as gp
from matplotlib import pyplot as plt
import numpy as np

class Instance:
    def __init__(self,n):
        random.seed(11)
        self.n = n
        self.points = []
        for i in range(n):
            self.points.append([random.randint(0,100),random.randint(0,100)])
        self.cost = [[0] * n for i in range(n)]
        for i in range(n):
            for j in range(i+1,n):
                #マンハッタン距離
                self.cost[i][j] = math.fabs(self.points[i][0]-self.points[j][0]) + math.fabs(self.points[i][1]-self.points[j][1])
                self.cost[j][i] = math.fabs(self.points[i][0]-self.points[j][0]) + math.fabs(self.points[i][1]-self.points[j][1])
                # #ユークリッド距離
                # self.cost[i][j] = math.sqrt(math.fabs(self.points[i][0]-self.points[j][0])**2 + math.fabs(self.points[i][1]-self.points[j][1])**2)
                # self.cost[j][i] = math.sqrt(math.fabs(self.points[i][0]-self.points[j][0])**2 + math.fabs(self.points[i][1]-self.points[j][1])**2)

class Solve:
    #昇順
    def initial_route1(self,instance):
        route = list(range(instance.n))
        return route
    #ランダム
    def initial_route2(self,instance):
        route = list(range(instance.n))
        random.shuffle(route)
        return route
    #貪欲法
    def initial_route3(self,instance):
        route = [0]
        for i in range(instance.n-1):
            copy_list = instance.cost[route[-1]].copy()
            for j in route:
                copy_list[j] = 9999
            index = copy_list.index(min(copy_list))
            route.append(index)
        return route
    def cal_cost(self,route,instance):
        sum_cost = 0
        n = instance.n
        for i in range(n - 1):
            sum_cost += instance.cost[route[i]][route[i + 1]]
        sum_cost += instance.cost[route[n - 1]][route[0]]
        return sum_cost
    def get_cost(self, index_i, index_j, route, instance):
        if(index_i == instance.n):
            index_i = 0
        if(index_j == instance.n):
            index_j = 0
        return instance.cost[route[index_i]][route[index_j]]
    #交換近傍
    def cal_neighbor1(self, index_i, index_j, route, instance):
        n = instance.n
        ### i,j:都市のID
        ### index_i,index_j:route上の都市i,jのインデクス
        delta = 0
        ### 隣接する場合
        if(index_i == index_j - 1 or index_i == index_j + n - 1):
            delta -= (self.get_cost(index_i - 1, index_i, route, instance) + self.get_cost(index_j, index_j + 1, route, instance))
            delta += (self.get_cost(index_i - 1, index_j, route, instance) + self.get_cost(index_i, index_j + 1, route, instance))
        elif(index_i == index_j + 1 or index_j == index_i + n - 1):
            delta -= (self.get_cost(index_j - 1, index_j, route, instance) + self.get_cost(index_i, index_i + 1, route, instance))
            delta += (self.get_cost(index_j - 1, index_i, route, instance) + self.get_cost(index_j, index_i + 1, route, instance))
        ### 隣接しない場合
        else:
            delta -= (self.get_cost(index_i - 1, index_i, route, instance) + self.get_cost(index_i, index_i + 1, route, instance))
            delta += (self.get_cost(index_j - 1, index_i, route, instance) + self.get_cost(index_i, index_j + 1, route, instance))
            delta -= (self.get_cost(index_j - 1, index_j, route, instance) + self.get_cost(index_j, index_j + 1, route, instance))
            delta += (self.get_cost(index_i - 1, index_j, route, instance) + self.get_cost(index_j, index_i + 1, route, instance))
        return delta
    #交換近傍を用いた近傍探索
    def local_search1(self, ini_route, iteration, instance):
        n = instance.n
        best = 999999
        local = self.cal_cost(ini_route,instance)
        best = min(best, local)
        #### search
        route = ini_route.copy()
        best_route = ini_route.copy()
        neighbors = dict()
        iteration_values = [0]*iteration
        for k in range(iteration):
            #近傍解を列挙
            for index_i in range(n):
                for index_j in range(index_i + 1, n):
                    neighbors[str(index_i)+','+str(index_j)] = self.cal_neighbor1(index_i, index_j, route, instance)
            sorted_neighbors = sorted(neighbors.items(), key = lambda item : item[1])
            flag = True
            for neighbor in sorted_neighbors:
                #最もよい近傍に遷移
                nids = neighbor[0].split(',')
                nid_index_i = int(nids[0])
                nid_index_j = int(nids[1])
                delta = neighbor[1]
                if(delta < 0):
                    flag = False
                    local += delta
                    break
            #遷移がなければ終了
            if flag:
                iteration_values[k:] = [best]*(iteration-k)
                break
            #解の更新
            index_i = nid_index_i
            index_j = nid_index_j
            i = route[index_i]
            j = route[index_j]
            route.pop(index_i)
            route.insert(index_i, j)
            route.pop(index_j)
            route.insert(index_j, i)
            if(local < best):
                best = local
                best_route = route.copy()
            iteration_values[k] = best
            neighbors.clear()
        result = dict()
        result['tour'] = str(best_route)
        result['cost'] = best
        result['iteration_values'] = iteration_values
        return result
    #タブーリスト
    def tabu_append(self, tabu_length, tabu_list, opration):
        if len(tabu_list) >= tabu_length:
            tabu_list.pop(0)
        tabu_list.append(opration)
        # tabu_list.append([opration[1],opration[0]])
        return tabu_list
    #交換近傍を用いたタブーサーチ
    def tabu_search1(self, ini_route, iteration, instance, tabu_length):
        n = instance.n
        tabu_list = list()
        best = 999999
        local = self.cal_cost(ini_route,instance)
        best = min(best, local)
        #### search
        route = ini_route.copy()
        best_route = ini_route.copy()
        neighbors = dict()
        iteration_values = [0]*iteration
        for k in range(iteration):
            #近傍解を列挙
            for index_i in range(n):
                for index_j in range(index_i + 1, n):
                    neighbors[str(index_i)+','+str(index_j)] = self.cal_neighbor1(index_i, index_j, route, instance)
            sorted_neighbors = sorted(neighbors.items(), key = lambda item : item[1])
            flag = False
            for neighbor in sorted_neighbors:
                nids = neighbor[0].split(',')
                nid_index_i = int(nids[0])
                nid_index_j = int(nids[1])
                nid_i = route[nid_index_i]
                nid_j = route[nid_index_j]
                if [nid_i, nid_index_i, nid_j, nid_index_j] not in tabu_list:
                    #最もよい近傍に遷移
                    delta = neighbor[1]
                    local += delta
                    flag = True
                    break
            if flag:
                #解の更新
                index_i = nid_index_i
                index_j = nid_index_j
                i = route[index_i]
                j = route[index_j]
                route.pop(index_i)
                route.insert(index_i, j)
                route.pop(index_j)
                route.insert(index_j, i)
                #タブーリストに記憶
                #opration : [都市i,都市iのインデクス,都市j,都市jのインデクス]
                opration = [i, index_i, j, index_j]
                tabu_list = self.tabu_append(tabu_length, tabu_list, opration)
            if(local < best):
                best = local
                best_route = route.copy()
            iteration_values[k] = best
            neighbors.clear()
        result = dict()
        result['tour'] = str(best_route)
        result['cost'] = best
        result['iteration_values'] = iteration_values
        return result
    #2-opt近傍
    def cal_neighbor2(self, index_i, index_j, route, instance):
        n = instance.n
        ### i,j:都市のID
        ### index_i,index_j:route上の都市i,jのインデクス
        ### index_i < index_j
        delta = 0
        if index_i == 0 and index_j == n - 1:
            delta = 0
        else:
            delta -= (self.get_cost(index_i - 1, index_i, route, instance) + self.get_cost(index_j, index_j + 1, route, instance))
            delta += (self.get_cost(index_i - 1, index_j, route, instance) + self.get_cost(index_i, index_j + 1, route, instance))
        return delta
    #2-opt近傍を用いた近傍探索
    def local_search2(self, ini_route, iteration, instance):
        n = instance.n
        best = 999999
        local = self.cal_cost(ini_route,instance)
        best = min(best, local)
        #### search
        route = ini_route.copy()
        best_route = ini_route.copy()
        neighbors = dict()
        iteration_values = [0]*iteration
        for k in range(iteration):
            #近傍解を列挙
            for index_i in range(n):
                for index_j in range(index_i + 1, n):
                    neighbors[str(index_i)+','+str(index_j)] = self.cal_neighbor2(index_i, index_j, route, instance)
            sorted_neighbors = sorted(neighbors.items(), key = lambda item : item[1])
            flag = True
            for neighbor in sorted_neighbors:
                #最もよい近傍に遷移
                nids = neighbor[0].split(',')
                nid_index_i = int(nids[0])
                nid_index_j = int(nids[1])
                delta = neighbor[1]
                if(delta < 0):
                    flag = False
                    #print(delta)
                    local += delta
                    break
            #遷移がなければ終了
            if flag:
                iteration_values[k:] = [best]*(iteration-k)
                break
            #解の更新
            index_i = nid_index_i
            index_j = nid_index_j
            rev = route[index_i : index_j + 1]
            rev.reverse()
            route = route[:index_i] + rev + route[index_j + 1:]
            if(local < best):
                best = local
                best_route = route.copy()
            iteration_values[k] = best
            neighbors.clear()
        result = dict()
        result['tour'] = str(best_route)
        result['cost'] = best
        result['iteration_values'] = iteration_values
        return result
    #2-opt近傍用タブーリスト
    def tabu_append2(self, tabu_length, tabu_list, opration):
        if len(tabu_list) >= tabu_length:
            tabu_list.pop(0)
        tabu_list.append(opration[0])
        tabu_list.append(opration[1])
        # tabu_list.append([opration[1],opration[0]])
        return tabu_list
    #2-opt近傍を用いたタブーサーチ
    def tabu_search2(self, ini_route, iteration, instance, tabu_length):
        n = instance.n
        tabu_list = list()
        best = 999999
        local = self.cal_cost(ini_route,instance)
        best = min(best, local)
        #### search
        route = ini_route.copy()
        best_route = ini_route.copy()
        neighbors = dict()
        iteration_values = [0]*iteration
        for k in range(iteration):
            #近傍解を列挙
            for index_i in range(n):
                for index_j in range(index_i + 1, n):
                    neighbors[str(index_i)+','+str(index_j)] = self.cal_neighbor2(index_i, index_j, route, instance)
            sorted_neighbors = sorted(neighbors.items(), key = lambda item : item[1])
            flag = False
            for neighbor in sorted_neighbors:
                nids = neighbor[0].split(',')
                nid_index_i = int(nids[0])
                nid_index_j = int(nids[1])
                in1, in2, in3, in4 = index_i-1,index_i,index_j,index_j+1
                if not (in2 == 0) and (in4 == n):
                    if in4 == n:
                        in4 = 0
                    if not ([route[in1], route[in2]] in tabu_list)or([route[in3], route[in4]] in tabu_list)or(neighbor[1] >= 0):
                        #最もよい近傍に遷移
                        delta = neighbor[1]
                        local += delta
                        flag = True
                        break
            if flag:
                #解の更新
                index_i = nid_index_i
                index_j = nid_index_j
                #タブーリストに記憶
                #opration : [禁止辺]
                if not (index_i == 0) and (index_j == n - 1):
                    opration = [[route[index_i-1], route[index_i]],[route[index_j], route[index_j + 1]]]
                rev = route[index_i : index_j + 1]
                rev.reverse()
                route = route[:index_i] + rev + route[index_j + 1:]
                if not (index_i == 0) and (index_j == n - 1):
                    tabu_list = self.tabu_append2(tabu_length, tabu_list, opration)
            if(local < best):
                best = local
                best_route = route.copy()
            iteration_values[k] = best
            neighbors.clear()
        result = dict()
        result['tour'] = str(best_route)
        result['cost'] = best
        result['iteration_values'] = iteration_values
        return result
    #Gurobiを用いた厳密解法
    def Gurobi(self,instance,iteration):
        n = instance.n
        cost = np.array(instance.cost)
        #the big M
        M = 10000
        tsp = gp.Model("traveling_salesman")
        tsp.Params.outputFlag = 0
        x = tsp.addVars(n, n, vtype=gp.GRB.BINARY, name = "x")
        u = tsp.addVars(n, name = "u")
        # Set objective
        tsp.setObjective( gp.quicksum(cost[i,j]*x[i,j] for i in range(n) for j in range(n)), gp.GRB.MINIMIZE)
        # Assignment constraints:
        tsp.addConstrs(( gp.quicksum(x[i,j] for j in range(n)) == 1 for i in range(n) ))         
        tsp.addConstrs(( gp.quicksum(x[i,j] for i in range(n)) == 1 for j in range(n) ))
        # Subtour-breaking constraints:
        tsp.addConstrs(( u[i] + 1 - u[j] <= M*(1 - x[i,j])  for i in range(n) for j in range(1,n) ))
        # Solving the model
        tsp.optimize()
        result = dict()
        print("厳密解　コスト",tsp.ObjVal)
        result['cost'] = tsp.ObjVal
        iteration_values = [tsp.ObjVal] * iteration
        result['iteration_values'] = iteration_values
        return result
    #結果のプロット
    def plot(self,local_result1,tabu_result1,local_result2,tabu_result2,gurobi_result,iteration):
        fig, ax = plt.subplots()
        x = list(range(iteration))
        y1 = local_result1['iteration_values']
        y2 = tabu_result1['iteration_values']
        y3 = local_result2['iteration_values']
        y4 = tabu_result2['iteration_values']
        y5 = gurobi_result['iteration_values']
        ax.set_xlabel('iteration')  # x軸ラベル
        ax.set_ylabel('cost')  # y軸ラベル
        ax.set_title('Shifting costs of solutions') # グラフタイトル
        l1,l2,l3,l4,l5 = "local search1","tabu search1","local search2","tabu search2","exact_cost"
        ax.plot(x, y1, label = l1)
        ax.plot(x, y2, label = l2)
        ax.plot(x, y3, label = l3)
        ax.plot(x, y4, label = l4)
        ax.plot(x, y5, label = l5)
        ax.legend(loc = 0)
        plt.show()

def main():
    probrem_size = 30
    tabu_length = 30
    instance = Instance(probrem_size)
    iteration = 100
    solve = Solve()
    ini_route1 = solve.initial_route1(instance)
    ini_routes = [ini_route1]
    # ini_route2 = solve.initial_route2(instance)
    # ini_route3 = solve.initial_route3(instance)
    # ini_routes = [ini_route1,ini_route2,ini_route3]
    for ini_route in ini_routes:
        t = time.time()
        local_result1 = solve.local_search1(ini_route, iteration, instance)
        print("交換近傍を用いた局所探索")
        # print(local_result1['tour'])
        print('目的関数値 : '+str(local_result1['cost']))
        print(time.time()-t,'(s)')
        print()
        
        t = time.time()
        tabu_result1 = solve.tabu_search1(ini_route, iteration, instance, tabu_length)
        print("交換近傍を用いたタブーサーチ")
        # print(tabu_result1['tour'])
        print('目的関数値 : '+str(tabu_result1['cost']))
        print(time.time()-t,'(s)')
        print()
        
        t = time.time()
        local_result2 = solve.local_search2(ini_route, iteration, instance)
        print("2-opt近傍を用いた局所探索")
        # print(local_result2['tour'])
        print('目的関数値 : '+str(local_result2['cost']))
        print(time.time()-t,'(s)')
        print()
        
        t = time.time()
        tabu_result2 = solve.tabu_search2(ini_route, iteration, instance, tabu_length)
        print("2-opt近傍を用いたタブーサーチ")
        # print(tabu_result2['tour'])
        print('目的関数値 : '+str(tabu_result2['cost']))
        print(time.time()-t,'(s)')
        print()
        
        gurobi_result = solve.Gurobi(instance,iteration)
        solve.plot(local_result1,tabu_result1,local_result2,tabu_result2,gurobi_result,iteration)
    
if __name__ == '__main__':
    main()