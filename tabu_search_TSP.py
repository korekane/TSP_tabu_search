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

class Instance:
    def __init__(self,n):
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
    def initial_route(self,instance):
        route = list(range(instance.n))
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
    def cal_neighbor(self, index_i, index_j, route, instance):
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
    def local_search(self, ini_route, iteration, instance):
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
                    neighbors[str(index_i)+','+str(index_j)] = self.cal_neighbor(index_i, index_j, route, instance)
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
    
    def tabu_append(self, tabu_length, tabu_list, opration):
        if len(tabu_list) >= tabu_length:
            tabu_list.pop(0)
        tabu_list.append(opration)
        # tabu_list.append([opration[1],opration[0]])
        return tabu_list
    def tabu_search(self, ini_route, iteration, instance, tabu_length):
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
                    neighbors[str(index_i)+','+str(index_j)] = self.cal_neighbor(index_i, index_j, route, instance)
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
                #opration : [都市iのインデクス,都市jのインデクス]
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
    def Gurobi(self,instance,iteration):
        model = gp.Model(name='TSP')
        model.Params.outputFlag = 0
        n = instance.n
        x = [[0] * n for i in range(n)]
        cost = [[0] * n for i in range(n)]
        for i in range(n):
            for j in range(i+1,n):
                x[i][j] = model.addVar(lb = 0, ub = 1, vtype = gp.GRB.BINARY,name='x'+str(i)+'_'+str(j))
                x[j][i] = x[i][j]
                cost[i][j] = instance.cost[i][j]
                cost[j][i] = cost[i][j]
        u = [0] * n
        for i in range(n):
            u[i] = model.addVar(lb = 1, ub = n - 1, vtype = gp.GRB.INTEGER,name='u'+str(i))
        model.setObjective(gp.quicksum((cost[i][j]*x[i][j] for i in range(n) for j in range(i,n))))
        for index in range(n):
            model.addConstr(gp.quicksum(x[i][index] for i in range(n)) == 1,name = "con1_"+str(index))
        for index in range(n):
            model.addConstr(gp.quicksum(x[index][j] for j in range(n)) == 1,name = "con2_"+str(index))
        BigM = 99999
        for i in range(n):
            for j in range(i+1,n):
                model.addConstr(u[i] + 1.0 - BigM * (1.0 - x[i][j]) <= u[j],name = "con3_"+str(i)+"_"+str(j))
        model.update()
        model.optimize()
        result = dict()
        result['cost'] = model.ObjVal
        iteration_values = [model.ObjVal] * iteration
        result['iteration_values'] = iteration_values
        return result
    
    def plot(self,local_result,tabu_result,gurobi_result,iteration):
        fig, ax = plt.subplots()
        x = list(range(iteration))
        y1 = local_result['iteration_values']
        y2 = tabu_result['iteration_values']
        y3 = gurobi_result['iteration_values']
        ax.set_xlabel('iteration')  # x軸ラベル
        ax.set_ylabel('cost')  # y軸ラベル
        ax.set_title('Shifting costs of solutions') # グラフタイトル
        l1,l2,l3 = "local_cost","tabu_cost","exact_cost"
        ax.plot(x, y1, label = l1)
        ax.plot(x, y2, label = l2)
        ax.plot(x, y3, label = l3)
        ax.legend(loc = 0)
        plt.show()

def main():
    probrem_size = 20
    tabu_length = 10
    instance = Instance(probrem_size)
    iteration = 50
    solve = Solve()
    ini_route = solve.initial_route(instance)
    t = time.time()
    local_result = solve.local_search(ini_route, iteration, instance)
    #print(result['tour'])
    print(local_result['cost'])
    print(time.time()-t,'(s)')
    print()
    t = time.time()
    tabu_result = solve.tabu_search(ini_route, iteration, instance, tabu_length)
    #print(result['tour'])
    print(tabu_result['cost'])
    print(time.time()-t,'(s)')
    gurobi_result = solve.Gurobi(instance,iteration)
    solve.plot(local_result,tabu_result,gurobi_result,iteration)
    
if __name__ == '__main__':
    main()