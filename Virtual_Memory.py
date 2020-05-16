'''
s is the segment number
p is page number
w is offset within page
PM[]是一个list 有524288个位置
PM[2s]是size of s
PM[2s+1]是frame number of PT
PA = PM[PM[2s+1]*512+p]*512+w

有2 lines 来initialize整个table
1：s,z,f 用来define Segmentation Table--ST ===> 用来assign ST的size，assign ST的frame
        --> s: PT of segments s
            z: length of segments s
            f: frame number, where s resides
        如果有line 1: 6,3000,4就是 segment6在frame4有size3000
                            -->
                                PM[2*6] == PM[12] = 3000, PM[2s+1] == PM[13] = 4(frame)

2: s,p,f 用来define Page Table--PT ===> 其实是用来assign Page Table的frame number
        --> s: segment s
            p: page number
            f: frame number
        如果有line 2: 6,5,9就是segment 6 在page 5 在frame 9
                    -->
                        PM[2*6+1] == PM[13] == 4(从line1得到）
                        PM[PM[2*6+1]*512 + page] == PM[PM[13]*512+5]
                                                == PM[4*512+5] == PM[2053] = 9(frame number);

#################################################
extension中，会多一个 Paging Disk(后续再讨论)
Page 可能不在PM中，ST中有负数，frame number f 会是负数
需要Keep tracking empty frame
#################################################
Paging Disk是一个2D Array DM, DM 是一个2d list with 'number of blocks' * 'block size’ =  1024*512,
which means DM 是一个有width 512 和 height 1024的 2D list。
当我们从 “initialize line1” 中得知了frame是一个负数的时候，说明这个PT不在PM中，这时候可以通过frame f的绝对值
来得到|f| = b，这里b就是block number， 可以通过b，再在DM中得到PT (这是ST entry)
当我们从 “initialize line2” 中得到了frame是一个负数的时候，同样的，|f| = b，可移动DM中得到page（PT Entry）
#################################################
initialize的时候，对line1与前没有改变：
1：s,z,f 用来define Segmentation Table--ST ===> 用来assign ST的size，assign ST的frame
        --> s: PT of segments s
            z: length of segments s
            f: frame number, where s resides
        如果有line 1: 8,4000,3 9,5000,-7就是 segment6在frame4有size3000,
                                        但是segment9的frame是-7，意味着它在DM中需要赋值，
                                        但是在这里不做改变，这里可以知道DM[|-7|] == DM[7]是page table of segment9
                            -->
                                PM[2*8] == PM[16] = 4000, PM[2s+1] == PM[17] = 3(frame)
                                PM[2*9] == PM[18] = 5000, PM[2s+1] == PM[19] = -7(frame)
但是line2 就开始改变了
2: s,p,f 用来define Page Table--PT ===> 其实是用来assign Page Table的frame number
        --> s: segment s
            p: page number
            f: frame number
        如果有line 2: 8,0,10 8,1,-20, 9,0,13 9,1,-25
                    -->
                        1.  PM[2*8+1] == PM[17] == 3(从line1得到）
                            PM[PM[2*8+1]*512 + page] == PM[PM[17]*512+0]
                                                == PM[3*512+0] == PM[1536] = 10(frame number);
                        2. PM[2*8+1] == PM[17] == 3
                           PM[PM[2*8+1]*512 + page] == PM[PM[17]*512+1]
                                                == PM[3*512+1] == PM[1537] = -20(frame number);
                            #####重点来了！######
                            这里的-20意味着什么？ 我们可以从-20得到他的绝对值20，然后知道了segment8 有page1，
                            所以得到segment8的page1 不在目前的PM里，而是应该在 DM的DM[20]
                        3. PM[9*2+1] == PM[19] == -7
                           因为这里是-7，所以其实segment9 的page table应该在DM[7]中，因为page是0，
                           所以DM[7][0] = 13
                        4. PM[9*2+1] == PM[19] == -7
                           和第三步一样，Segment9的page1是在DM[7]中。所以DM[7][1] = -25
#################################################
从VA中得到了
s is the segment number
p is page number
w is offset within page
和pw
通过VA 来找 PA，在initialize之后 -->
1. if pw >= PM[2s] : report error
   else:    continue
2. if PM[2s+1](就是initialize之后的ST的frame) < 0:
       a.找出free的frame f
       b.更新free frame list
       c.从DM中读数放入PM（后续再更新）======================= 
                                   通过 PM[2s+1] 的绝对值（ST的frame，因为是负数，加上绝对值）得到 b，
                                   通过之前2步得到的 新的free frame f，
                                   现在有b和f
                                   ---> 从DM中读b，放入PM[f*512](需要再次更新。。)
       d.PM[2s+1] = f 给PM[2s+1]附上新的frame值，这里的frame是找出free 的frame f
    ###第二步都是在update ST entry
3. else if PM[PM[2s+1]*512 + p]（就是initialize之后PT的frame）<0：
       a.找出free的frame f
       b.更新free frame list
       c.从DM中读数放入PM（后续再更新）=======================
       d.PM[PM[2s+1]*512 + p] = f 附上新的frame值
    ###第三步都是在update PT entry
4. 可以找出PA了， PA = PM[PM[2s+1]*512 + p]*512 + w ==>这就是要return的值
#########################################
举例说明：
1.都是resident 就不说了
2.PT is resident，但是page不是：
    假设s = 8, p = 1, w = 10
    a. PM[2*8+1] == 3,这里没问题
    b. PM[3*512+1] == -20，就有问题了：
                        这说明page在disk block 20(DM[20])
    c.找出 free的frame，与-20替换，假设这里frame是4，那么就有 PM[3*512+1] = 4
    d.此时可以找出PA = 4*512+10 = 2058
3.PT is not resident, but page is
    假设 s = 9,p = 0, w = 10
    a.PM[2*9+1] == PM[19] = -7,这里有问题
                        这说明需要找DM[7]里的东西
    b.从free的frame找出f与-7替换。这里假设 f = 5，那么就有PM[2*9+1] == PM[19] = 5
    c.然后要整个copy DM[7]那一整行 到 PM[5*512]中
    d.找出PM[5*512+P] = PM[2560+0] == 13,这里的13是从DM中copy过来的
    e.最后可以得到PA = 13*512+w = 6656+10 = 6666
4.都不是resident
    假设s = 9,p = 1, w = 10
    a.PM[2*9+1] == PM[19] = -7,这里有问题
                        这说明需要找DM[7]里的东西
    b.从free的frame找出f与-7替换。这里假设 f = 5，那么就有PM[2*9+1] == PM[19] = 5
    c.然后要整个copy DM[7]那一整行 到 PM[5*512]中 PM[2560] = DM[7](每一个都要copy，想一下怎么做到)
    d.PM[2560+p] = PM[2560+1] = PM[2561] == -25 ，-25 是copy过来的，这里又有问题了
                        这说明要再找一个frame来替换这个-25
    e.找出free的frame f，假设这里是f = 14，于是替换 PM[2561] = 14
    f.这里可以找出需要的PA = 14*512 + 10 = 7178
'''
from asyncore import write

def get_initialize(initialize:list)->list:
    get_init = []
    while(len(initialize)!=0):
        l_3 = []
        for i in range(3):
            l_3.append(initialize[0])
            initialize.pop(0)
        get_init.append(l_3)
    return get_init
    
#l = get_initialize(initialize)
#print(l)

def DeciToBin(dec:str)-> str:
    dec_int = int(dec)
    return bin(dec_int)[2:].zfill(27)
#print(DeciToBin('789002'))

def ConvertVAtoSPWandPW(bin_str:str)->list: 
    SPW_list = []
    #print(bin_str)
    SPW_list.append(int(bin_str[0:9],2))
    SPW_list.append(int(bin_str[9:18],2))
    SPW_list.append(int(bin_str[18:27],2))
    SPW_list.append(int(bin_str[9:27],2))
    return SPW_list  
#print(ConvertVAtoSPWandPW(DeciToBin('1575864')))       

def initialize_frist(PM:list, first_as3:list,free_frame:list):
    '''
    1：s,z,f 用来define Segmentation Table--ST ===> 用来assign ST的size，assign ST的frame
        --> s: PT of segments s
            z: length of segments s
            f: frame number, where s resides
        如果有line 1: 8,4000,3 9,5000,-7就是 segment6在frame4有size3000,
                                        但是segment9的frame是-7，意味着它在DM中需要赋值，
                                        但是在这里不做改变，这里可以知道DM[|-7|] == DM[7]是page table of segment9
                            -->
                                PM[2*8] == PM[16] = 4000, PM[2s+1] == PM[17] = 3(frame)
                                PM[2*9] == PM[18] = 5000, PM[2s+1] == PM[19] = -7(frame)
    '''
    for i in first_as3:
        s,z,f = i[0],i[1],i[2]
        if f>0:
            free_frame.remove(f)
        PM[2*s] = z
        PM[2*s+1] = f

def initialize_second(PM:list, DM:list, second_as3:list,free_frame:list):
    '''
    但是line2 就开始改变了
    2: s,p,f 用来define Page Table--PT ===> 其实是用来assign Page Table的frame number
        --> s: segment s
            p: page number
            f: frame number
        如果有line 2: 8,0,10 8,1,-20, 9,0,13 9,1,-25
                    -->
                        1.  PM[2*8+1] == PM[17] == 3(从line1得到）
                            PM[PM[2*8+1]*512 + page] == PM[PM[17]*512+0]
                                                == PM[3*512+0] == PM[1536] = 10(frame number);
                        2. PM[2*8+1] == PM[17] == 3
                           PM[PM[2*8+1]*512 + page] == PM[PM[17]*512+1]
                                                == PM[3*512+1] == PM[1537] = -20(frame number);
                            #####重点来了！######
                            这里的-20意味着什么？ 我们可以从-20得到他的绝对值20，然后知道了segment8 有page1，
                            所以得到segment8的page1 不在目前的PM里，而是应该在 DM的DM[20]
                        3. PM[9*2+1] == PM[19] == -7
                           因为这里是-7，所以其实segment9 的page table应该在DM[7]中，因为page是0，
                           所以DM[7][0] = 13
                        4. PM[9*2+1] == PM[19] == -7
                           和第三步一样，Segment9的page1是在DM[7]中。所以DM[7][1] = -25
    '''
    for i in second_as3:
        s,p,f = i[0],i[1],i[2]
        if f>0:
            free_frame.remove(f)
        ST_frame = PM[2*s+1]
        if ST_frame >= 0:
            PM[ST_frame*512 + p] = f

        else:
            DM[abs(ST_frame)][p] = f
def get_PA(PM:list,DM:list,free_frame:list,input_line:list):
    '''
    1.都是resident 就不说了
    2.PT is resident，但是page不是：
        假设s = 8, p = 1, w = 10
        a. PM[2*8+1] == 3,这里没问题
        b. PM[3*512+1] == -20，就有问题了：
                            这说明page在disk block 20(DM[20])
        c.找出 free的frame，与-20替换，假设这里frame是4，那么就有 PM[3*512+1] = 4
        d.此时可以找出PA = 4*512+10 = 2058
    3.PT is not resident, but page is
        假设 s = 9,p = 0, w = 10
        a.PM[2*9+1] == PM[19] = -7,这里有问题
                            这说明需要找DM[7]里的东西
        b.从free的frame找出f与-7替换。这里假设 f = 5，那么就有PM[2*9+1] == PM[19] = 5
        c.然后要整个copy DM[7]那一整行 到 PM[5*512]中
        d.找出PM[5*512+P] = PM[2560+0] == 13,这里的13是从DM中copy过来的
        e.最后可以得到PA = 13*512+w = 6656+10 = 6666
    4.都不是resident
        假设s = 9,p = 1, w = 10
        a.PM[2*9+1] == PM[19] = -7,这里有问题
                            这说明需要找DM[7]里的东西
        b.从free的frame找出f与-7替换。这里假设 f = 5，那么就有PM[2*9+1] == PM[19] = 5
        c.然后要整个copy DM[7]那一整行 到 PM[5*512]中 PM[2560] = DM[7](每一个都要copy，想一下怎么做到)
        d.PM[2560+p] = PM[2560+1] = PM[2561] == -25 ，-25 是copy过来的，这里又有问题了
                            这说明要再找一个frame来替换这个-25
        e.找出free的frame f，假设这里是f = 14，于是替换 PM[2561] = 14
        f.这里可以找出需要的PA = 14*512 + 10 = 7178
    '''
    PA_list = []
    for each_VA in input_line:
        SPWPW = ConvertVAtoSPWandPW(DeciToBin(str(each_VA)))
        s,p,w,pw = SPWPW[0],SPWPW[1],SPWPW[2],SPWPW[3]
        if pw>=PM[2*s]:
            #print("error")
            PA_list.append('-1')
            continue
        #print(s," ",p," ",w," ",pw,"\n")
        ST_frame = PM[2*s+1]
        if ST_frame <=0:
            things_in_DM = DM[abs(ST_frame)]
            free_f = free_frame[0]
            free_frame.pop(0)
            PM[2*s+1] = free_f
            #print("len of things in DM(should be 512): ",len(things_in_DM))
            for i in range(512):
                PM[free_f*512+i] = things_in_DM[i]
        PT_frame = PM[PM[2*s+1]*512 +p]
        if PT_frame <= 0:
            free_f = free_frame[0]
            free_frame.pop(0)
            PM[PM[2*s+1]*512 +p] = free_f
        PA_list.append(str(PM[PM[2*s+1]*512 + p]*512 + w))
    return PA_list
            
            
        
        
        
      
if __name__ == '__main__':
    mark_as_empty = 999999999999
    total_length = 524288
    PM = [mark_as_empty]*total_length
    disk_w = 512
    disk_h = 1024
    DM = [[mark_as_empty for x in range(disk_w)] for y in range(disk_h)] 
    free_frame = []
    for i in range(2,1024):
        free_frame.append(i)  
    ###########################
    '''
    这里会被input file改掉
    ############################
    '''
    #first_line = [8,4000,3,9,5000,-7]
    #second_line = [8,0,10,8,1,-20,9,0,13,9,1,-25]
    #input_line = [2097162,2097674,2359306,2359818]
    '''
    ############################
    '''
    init_path = input("Enter the init file's path:")
    input_path = input("Enter the input file's path:")
    
    file_init = open(init_path,"r")#'/Users/alexhu/Desktop/init-dp.txt',"r")
    #file_init = open('/Users/alexhu/Desktop/init-dp.txt',"r")
    init_lines = file_init.readlines()
    file_init.close()
    
    first_line_str = init_lines[0].split()
    first_line = []
    for i in first_line_str:
        first_line.append(int(i))
        
    second_line_str = init_lines[1].split()
    second_line = []
    for i in second_line_str:
        second_line.append(int(i))
    
    file_input = open(input_path,"r")#'/Users/alexhu/Desktop/input-dp.txt',"r")
    #file_input = open('/Users/alexhu/Desktop/input-dp.txt',"r")
    input_lines = file_input.readlines()
    file_input.close()
    input_line_str = input_lines[0].split()
    input_line = []
    for i in input_line_str:
        input_line.append(int(i))
    
    

    
    
    
    first_as3 = get_initialize(first_line)
    second_as3 = get_initialize(second_line)
    #print(first_as3,'\n',second_as3)
    
    initialize_frist(PM, first_as3,free_frame)
    #print(PM[16],PM[17],PM[18],PM[19])
    
    initialize_second(PM, DM, second_as3,free_frame)
    '''print(" ",PM[1536]," should be 10\n",
          PM[1537]," should be -20\n",
          PM[2560]," should be max\n",
          PM[2561]," should be max\n",
          DM[7][0]," should be 13\n",
          DM[7][0]," should be -25")'''
    l = get_PA(PM, DM, free_frame,input_line)
    
    #print(l)
    
    write_file = open("output-dp.txt","w+")
    write_str = " "
    write_file.write(write_str.join(l))
    write_file.close()
    print("The output file has correctly created under the same path of this python file.")
    

    
    
    
    
    
    
    
    
    