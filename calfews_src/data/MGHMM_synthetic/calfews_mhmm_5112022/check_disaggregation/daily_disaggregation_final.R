##Find historical daily proportions



### uncomment and run to get normalized inputs, then save and load back in future
calfews_data=read.csv("./inputs/calfews_src-data-sim-agg.csv",header=TRUE)

yearly_sum=aggregate(calfews_data,by=list(calfews_data$Year),FUN=sum)

for (j in 5:19){
  for (i in 1:40177){
    calfews_data[i,j]=calfews_data[i,j]/yearly_sum[which(calfews_data$Year[i]==yearly_sum$Group.1),j+1]
  }
}

write.csv(calfews_data,file="./inputs/calfews_src-data-sim-agg_norm.csv",append=TRUE,col.names = T, row.names = F,quote = FALSE)

### read in pre-normalized data
calfews_data=read.csv("./inputs/calfews_src-data-sim-agg_norm.csv",header=TRUE)

yearly_sum=aggregate(calfews_data,by=list(calfews_data$Year),FUN=sum)

#Import synthetic and historic annual flows

AnnualQ_s=read.csv("./outputs/AnnualQ_s.csv",header=FALSE,sep=',')
AnnualQ_h=read.csv("./inputs/AnnualQ_h.csv",header=FALSE,sep=',')

#Identify number of years in synthetic & historical sample
N_s=NROW(AnnualQ_s)
N_h=NROW(AnnualQ_h)


#Find closest year for each synthetic sample
index=numeric(N_s)

for (j in 1:N_s){
  distance=numeric(N_h)
  for (i in 1:N_h){
    distance[i]=(AnnualQ_s[j,1]-AnnualQ_h[i,1])^2
  }
  index[j]=which.min(distance)
}

#Assign year to the index
closest_year=yearly_sum$Group.1[index]

#Disaggregate to daily data
DailyQ_s=data.frame(calfews_data)
DailyQ_s=DailyQ_s[DailyQ_s$Year < DailyQ_s$Year[1] + N_s, ]

count=1
for (i in 1:N_s){
  y=unique(DailyQ_s$Year)[i]
  newdatasize <- dim(DailyQ_s[which(DailyQ_s$Year==unique(DailyQ_s$Year)[i]), ])[1]
  olddata <- calfews_data[ which(calfews_data$Year==closest_year[i]), ]
  for (z in 5:19){
    olddata[,z]=AnnualQ_s[i,z-4]*olddata[,z]
  }
  ## fill in data, accounting for leap years. assume leap year duplicates feb 29
  if (newdatasize == 365){
    if (dim(olddata)[1] == 365){
      DailyQ_s[count:(count+365-1),5:19]=olddata[,5:19]
    }else if (dim(olddata)[1] == 366){
      # if generated data has 365 days, and disaggregating 366-day series, skip feb 29 (60th day of leap year)
      DailyQ_s[count:(count+59-1),5:19]=olddata[1:59,5:19]
      DailyQ_s[(count+60-1):(count+365-1),5:19]=olddata[61:366,5:19]
    }
  }else if (newdatasize == 366){
    if (dim(olddata)[1] == 366){
      DailyQ_s[count:(count+366-1),5:19]=olddata[,5:19]
    }else if (dim(olddata)[1] == 365){
      # if generated data has 366 days, and disaggregating 365-day series, repeat feb 28 (59rd day of leap year)
      DailyQ_s[count:(count+59-1),5:19]=olddata[1:59,5:19]
      DailyQ_s[count+60-1,5:19]=olddata[59,5:19]
      DailyQ_s[(count+61-1):(count+366-1),5:19]=olddata[60:365,5:19]
    }
  }
  count=count+NROW(olddata)
}

write.csv(DailyQ_s,file="./outputs/DailyQ_s.csv",append=F,col.names = T, row.names = F,quote = FALSE)
