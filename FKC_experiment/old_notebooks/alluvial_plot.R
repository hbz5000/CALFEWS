library(ggplot2)
library(ggalluvial)
library(viridis)
library(gridExtra)
library(RColorBrewer)
library(wesanderson)

run_mode = 1   # 2 = 2 independent figs (b4, gains); 1 = combined fig
consistent_ylim_gainloss = 1    # 1 = gain/loss figs will have same ylim, 0 = no

# ##########################
# ## 3 panels of flows b4 improvement, separated by contract, season, wetness
# ############################
# left_pal <- colorRampPalette(plasma(9, begin=0.2,end=0.8))
# left_pal <-colorRampPalette(brewer.pal(9, 'YlOrRd')[2:8])
# left_pal <-colorRampPalette(wes_palette('Zissou1'))
# left_pal <-wes_palette('Cavalcanti1')
# left_pal <- c(left_pal[2],left_pal[4],left_pal[3],left_pal[1])
# left_pal <-wes_palette('Zissou1',4,type='continuous')
# left_pal <-wes_palette('Rushmore1')
# left_pal <- c(left_pal[1],left_pal[3],left_pal[4],left_pal[5])
left_pal <- wes_palette('Rushmore1',8,type='continuous')
left_pal <- c(left_pal[1],left_pal[4],left_pal[6],left_pal[7])

if (run_mode == 2) {
  if (consistent_ylim_gainloss == 0){
    ylim_gainloss <- NULL
    label_threshold <- c(150,150,150,1.5,2,1.33, 0.5,1,0.4)
  }else{
    ylim_gainloss <- c(0,61)
    label_threshold <- c(150,150,150,2,2,2,2,2,2)
  }
  gg_font <- c(7,8)
  label_font <- c(1.5,2.5)
  subfig <- c('a)','b)','c)','a)','b)','c)','d)','e)','f)')
}else{
  if (consistent_ylim_gainloss == 0){
    ylim_gainloss <- c(NULL,NULL,NULL,NULL,NULL,NULL)
    label_threshold <- c(200,200,200,2,2.6,2, 0.8,1.4,0.7)
  }else{
    ylim_gainloss <- cbind(c(0,40),c(0,40),c(0,61),c(0,61),c(0,45),c(0,45))
    label_threshold <- c(200,200,200,1.8,1.8,2.8,2.8,2,2)
  }
  gg_font <- c(8,8)
  label_font <- c(2,2)
  subfig <- c('a)','d)','g)','b)','c)','e)','f)','h)','i)')
}




##########################
## first get contract flows before project
############################

df <- read.csv('figures/alluvial_contract_b4.csv', header=TRUE, sep=',',
               colClasses=c('character','character','numeric','numeric','character'))

### order source
df$Source <- factor(df$Source, levels=c('+Friant', '+Local','+TableA','+Other'))

### order districts by total gain/loss
df$GainOrLoss = df$Magnitude * df$Sign
district_sum_gainloss = aggregate(df$Magnitude, by=list(District=df$District), FUN=sum)
district_sum_gainloss <- district_sum_gainloss[order(-district_sum_gainloss$x),]
district_order <- c('+F-1','+F-2','+F-3','+F-4','+F-5','+F-6','+F-7','+F-8','+F-9','+F-10',
                   '+F-11','+F-12','+F-13','+F-14','+F-15','+F-16',
                   '+O-1','+O-2','+O-3','+O-4','+O-5','+O-6','+O-7','+O-8','+O-9','+O-10',
                   '+O-11','+O-12','+O-13','+O-14','+O-15','+O-16','+O-17','+O-18','+O-19','+O-20',
                   '+O-21','+O-22','+O-23','+O-24','+O-25','+O-26','+O-27','+O-28','+O-29','+O-30',
                   '+O-31','+O-32','+O-33','+O-34','+O-35','+O-36','+O-37','+O-38','+O-39','+O-40')
df$District <- factor(df$District, levels = district_order)
df$District <- droplevels(df$District)
district_order <- levels(df$District)

### convert to long format (one row for each flow)
dflong <- to_lodes_form(df, key='WaterType', value='Group', id='Cohort', axes=c(1,2))

### get colors for columns
# group_colors <- rev(left_pal(4))
group_colors <- left_pal[1:4]
dflong_grps <- levels(dflong$Group)
district_sum_gainloss$color <- district_sum_gainloss$District
for (i in 1:length(district_sum_gainloss$District)){
  district_sum_gainloss$color[i] <- df$Color[df$District == district_sum_gainloss$District[i]][1]
}
district_colors <- district_sum_gainloss$color
for (i in 1:length(district_sum_gainloss$District)){
  d <- district_order[i]
  district_colors[i] <- district_sum_gainloss$color[district_sum_gainloss$District == d][1]
}
group_colors <- c(group_colors, district_colors)


### get labels for columns
dflong_label <- as.character(dflong$Group)
for (i in 1:length(dflong$Magnitude)){
  grp <- as.character(dflong$Group[i])
  grp_source <- sum(dflong$Magnitude[dflong$Group == grp])
  if (grp_source < label_threshold[1]){
    dflong_label[i] = ''
  }else{
    dflong_label[i] = substr(dflong_label[i],2,200)
  }
}
dflong$label = dflong_label


# plot with all strata colored
p1 <- ggplot(data = dflong,
             aes(x = WaterType, stratum = Group, alluvium = Cohort, y = GainOrLoss)) +
  theme_minimal(base_size= gg_font[1]) +
  theme(legend.position='none',rect = element_rect(size=3)) +
  geom_alluvium(aes(fill=Group), alpha=0.8) +
  geom_stratum(aes(fill=Group), alpha=1) +
  geom_text(stat = "stratum", aes(label = label), size= label_font[1], color='white') +
  scale_fill_manual(values=group_colors, breaks=dflong_grps, labels=dflong_grps) +
  ggtitle("") + xlab('') + ylab('Total deliveries (kAF/year)') +
  labs(tag = subfig[1]) +
  coord_cartesian(xlim=c(1.4,1.6), ylim=NULL)



######################
## now data split by season
#####################

df <- read.csv('figures/alluvial_season_b4.csv', header=TRUE, sep=',',
               colClasses=c('character','character','numeric','numeric','character'))

### get months
df$Season <- factor(df$Season, levels=c('+Oct-Dec','+Jan-Mar','+Apr-Jun','+Jul-Sep'))

### order districts by total gain/loss
df$GainOrLoss = df$Magnitude * df$Sign
district_sum_gainloss = aggregate(df$Magnitude, by=list(District=df$District), FUN=sum)
district_sum_gainloss <- district_sum_gainloss[order(-district_sum_gainloss$x),]
df$District = factor(df$District, levels = district_order)

### convert to long format (one row for each flow)
dflong <- to_lodes_form(df, key='WaterType', value='Group', id='Cohort', axes=c(1,2))

### get colors for columns
# group_colors <- rev(left_pal(4))
group_colors <- left_pal[1:4]
dflong_grps <- levels(dflong$Group)
district_sum_gainloss$color <- district_sum_gainloss$District
for (i in 1:length(district_sum_gainloss$District)){
  district_sum_gainloss$color[i] <- df$Color[df$District == district_sum_gainloss$District[i]][1]
}
district_colors <- district_sum_gainloss$color
for (i in 1:length(district_sum_gainloss$District)){
  d <- district_order[i]
  district_colors[i] <- district_sum_gainloss$color[district_sum_gainloss$District == d][1]
}
group_colors <- c(group_colors, district_colors)

### get labels for columns
dflong_label <- as.character(dflong$Group)
for (i in 1:length(dflong$Magnitude)){
  grp <- as.character(dflong$Group[i])
  grp_source <- sum(dflong$Magnitude[dflong$Group == grp])
  if (grp_source < label_threshold[2]){
    dflong_label[i] = ''
  }else{
    dflong_label[i] = substr(dflong_label[i],2,200)
  }
}
dflong$label = dflong_label


# plot with all strata colored
p2 <- ggplot(data = dflong,
             aes(x = WaterType, stratum = Group, alluvium = Cohort, y = GainOrLoss)) +
  theme_minimal(base_size= gg_font[1]) +
  theme(legend.position='none') +
  geom_alluvium(aes(fill=Group), alpha=0.8) +
  geom_stratum(aes(fill=Group), alpha=1) +
  geom_text(stat = "stratum", aes(label = label), size= label_font[1], color='white') +
  scale_fill_manual(values=group_colors, breaks=dflong_grps, labels=dflong_grps) +
  ggtitle("") + xlab('') + ylab('Total deliveries (kAF/year)') +
  labs(tag = subfig[2]) +
  coord_cartesian(xlim=c(1.4,1.6), ylim=NULL)




######################
## now data split by wateryear type/wetness
#####################

df <- read.csv('figures/alluvial_wetness_b4.csv', header=TRUE, sep=',',
               colClasses=c('character','character','numeric','numeric','character'))


### get quartile
df$HydroQuartile <- factor(df$HydroQuartile, levels=c('+q1','+q2','+q3','+q4'))

### order districts by total gain/loss
df$GainOrLoss = df$Magnitude * df$Sign
district_sum_gainloss = aggregate(df$Magnitude, by=list(District=df$District), FUN=sum)
district_sum_gainloss <- district_sum_gainloss[order(-district_sum_gainloss$x),]
df$District = factor(df$District, levels = district_order)

### convert to long format (one row for each flow)
dflong <- to_lodes_form(df, key='WaterType', value='Group', id='Cohort', axes=c(1,2))

### get colors for columns
# group_colors <- rev(left_pal(4))
group_colors <- left_pal[1:4]
dflong_grps <- levels(dflong$Group)
district_sum_gainloss$color <- district_sum_gainloss$District
for (i in 1:length(district_sum_gainloss$District)){
  district_sum_gainloss$color[i] <- df$Color[df$District == district_sum_gainloss$District[i]][1]
}
district_colors <- district_sum_gainloss$color
for (i in 1:length(district_sum_gainloss$District)){
  d <- district_order[i]
  district_colors[i] <- district_sum_gainloss$color[district_sum_gainloss$District == d][1]
}
group_colors <- c(group_colors, district_colors)

### get labels for columns
dflong_label <- as.character(dflong$Group)
for (i in 1:length(dflong$Magnitude)){
  grp <- as.character(dflong$Group[i])
  grp_source <- sum(dflong$Magnitude[dflong$Group == grp])
  if (grp_source < label_threshold[3]){
    dflong_label[i] = ''
  }else{
    dflong_label[i] = substr(dflong_label[i],2,200)
  }
}
dflong$label = dflong_label


# plot with all strata colored
p3 <- ggplot(data = dflong,
             aes(x = WaterType, stratum = Group, alluvium = Cohort, y = GainOrLoss)) +
  theme_minimal(base_size= gg_font[1]) +
  theme(legend.position='none') +
  geom_alluvium(aes(fill=Group), alpha=0.8) +
  geom_stratum(aes(fill=Group), alpha=1) +
  geom_text(stat = "stratum", aes(label = label), size= label_font[1], color='white') +
  scale_fill_manual(values=group_colors, breaks=dflong_grps, labels=dflong_grps) +
  ggtitle("") + xlab('') + ylab('Total deliveries (kAF/year)') +
  labs(tag = subfig[3]) +
  coord_cartesian(xlim=c(1.4,1.6), ylim=NULL)

################
if (run_mode == 2){
  g <- arrangeGrob(p1, p2, p3, nrow=1, ncol=3)
  ggsave('figures/alluvia_b4.jpg', g, width=7, height=3, units='in', dpi=500)
}






######################################################
#### now gains/losses plot
######################################################


### positive gains

df <- read.csv('figures/alluvial_contract.csv', header=TRUE, sep=',',
               colClasses=c('character','character','numeric','numeric','character'))
df <- df[df$Sign == 1,]

### order source
df$Source <- factor(df$Source, levels=c('+Friant', '+Local','+TableA','+Other'))

### order districts by total gain/loss
df$GainOrLoss = df$Magnitude * df$Sign
district_sum_gainloss = aggregate(df$Magnitude, by=list(District=df$District), FUN=sum)
district_sum_gainloss <- district_sum_gainloss[order(-district_sum_gainloss$x),]
district_order <- c('+F-1','+F-2','+F-3','+F-4','+F-5','+F-6','+F-7','+F-8','+F-9','+F-10',
                    '+F-11','+F-12','+F-13','+F-14','+F-15','+F-16',
                    '+O-1','+O-2','+O-3','+O-4','+O-5','+O-6','+O-7','+O-8','+O-9','+O-10',
                    '+O-11','+O-12','+O-13','+O-14','+O-15','+O-16','+O-17','+O-18','+O-19','+O-20',
                    '+O-21','+O-22','+O-23','+O-24','+O-25','+O-26','+O-27','+O-28','+O-29','+O-30',
                    '+O-31','+O-32','+O-33','+O-34','+O-35','+O-36','+O-37','+O-38','+O-39','+O-40')
df$District <- factor(df$District, levels = district_order)
df$District <- droplevels(df$District)
district_order <- levels(df$District)

### convert to long format (one row for each flow)
dflong <- to_lodes_form(df, key='WaterType', value='Group', id='Cohort', axes=c(1,2))

### get colors for columns
# group_colors <- rev(left_pal(4))
group_colors <- left_pal[1:4]
dflong_grps <- levels(dflong$Group)
district_sum_gainloss$color <- district_sum_gainloss$District
for (i in 1:length(district_sum_gainloss$District)){
  district_sum_gainloss$color[i] <- df$Color[df$District == district_sum_gainloss$District[i]][1]
}
district_colors <- district_sum_gainloss$color
for (i in 1:length(district_sum_gainloss$District)){
  d <- district_order[i]
  district_colors[i] <- district_sum_gainloss$color[district_sum_gainloss$District == d][1]
}
group_colors <- c(group_colors, district_colors)

### get labels for columns
dflong_label <- as.character(dflong$Group)
for (i in 1:length(dflong$Magnitude)){
  grp <- as.character(dflong$Group[i])
  grp_source <- sum(dflong$Magnitude[dflong$Group == grp])
  if (grp_source < label_threshold[4]){
    dflong_label[i] = ''
  }else{
    dflong_label[i] = substr(dflong_label[i],2,200)
  }
}
dflong$label = dflong_label


# plot with all strata colored
p4 <- ggplot(data = dflong,
             aes(x = WaterType, stratum = Group, alluvium = Cohort, y = Magnitude)) +
  theme_minimal(base_size= gg_font[2]) +
  theme(legend.position='none') +
  geom_alluvium(aes(fill=Group), alpha=0.8) +
  geom_stratum(aes(fill=Group), alpha=1) +
  geom_text(stat = "stratum", aes(label = label), size= label_font[2], color='white') +
  scale_fill_manual(values=group_colors, breaks=dflong_grps, labels=dflong_grps) +
  ggtitle("") + xlab('') + ylab('Gains (kAF/year)') +
  labs(tag = subfig[4]) +
  coord_cartesian(xlim=c(1.4,1.6), ylim=ylim_gainloss[,1])



### negative gains

df <- read.csv('figures/alluvial_contract.csv', header=TRUE, sep=',',
               colClasses=c('character','character','numeric','numeric','character'))
df <- df[df$Sign == -1,]

### order source
df$Source <- factor(df$Source, levels=c('-Friant', '-Local','-TableA','-Other'))

### order districts by total gain/loss
df$GainOrLoss = df$Magnitude * df$Sign
district_sum_gainloss = aggregate(df$Magnitude, by=list(District=df$District), FUN=sum)
district_sum_gainloss <- district_sum_gainloss[order(-district_sum_gainloss$x),]
district_order <- c('-F-1','-F-2','-F-3','-F-4','-F-5','-F-6','-F-7','-F-8','-F-9','-F-10',
                    '-F-11','-F-12','-F-13','-F-14','-F-15','-F-16',
                    '-O-1','-O-2','-O-3','-O-4','-O-5','-O-6','-O-7','-O-8','-O-9','-O-10',
                    '-O-11','-O-12','-O-13','-O-14','-O-15','-O-16','-O-17','-O-18','-O-19','-O-20',
                    '-O-21','-O-22','-O-23','-O-24','-O-25','-O-26','-O-27','-O-28','-O-29','-O-30',
                    '-O-31','-O-32','-O-33','-O-34','-O-35','-O-36','-O-37','-O-38','-O-39','-O-40')
df$District <- factor(df$District, levels = district_order)
df$District <- droplevels(df$District)
district_order <- levels(df$District)

### convert to long format (one row for each flow)
dflong <- to_lodes_form(df, key='WaterType', value='Group', id='Cohort', axes=c(1,2))

### get colors for columns
# group_colors <- rev(left_pal(4))
group_colors <- left_pal[1:4]
dflong_grps <- levels(dflong$Group)
district_sum_gainloss$color <- district_sum_gainloss$District
for (i in 1:length(district_sum_gainloss$District)){
  district_sum_gainloss$color[i] <- df$Color[df$District == district_sum_gainloss$District[i]][1]
}
district_colors <- district_sum_gainloss$color
for (i in 1:length(district_sum_gainloss$District)){
  d <- district_order[i]
  district_colors[i] <- district_sum_gainloss$color[district_sum_gainloss$District == d][1]
}
group_colors <- c(group_colors, district_colors)

### get labels for columns
dflong_label <- as.character(dflong$Group)
for (i in 1:length(dflong$Magnitude)){
  grp <- as.character(dflong$Group[i])
  grp_source <- sum(dflong$Magnitude[dflong$Group == grp])
  if (grp_source < label_threshold[5]){
    dflong_label[i] = ''
  }else{
    dflong_label[i] = substr(dflong_label[i],2,200)
  }
}
dflong$label = dflong_label


# plot with all strata colored
p5 <- ggplot(data = dflong,
             aes(x = WaterType, stratum = Group, alluvium = Cohort, y = Magnitude)) +
  theme_minimal(base_size= gg_font[2]) +
  theme(legend.position='none') +
  geom_alluvium(aes(fill=Group), alpha=0.8) +
  geom_stratum(aes(fill=Group), alpha=1) +
  geom_text(stat = "stratum", aes(label = label), size= label_font[2], color='white') +
  scale_fill_manual(values=group_colors, breaks=dflong_grps, labels=dflong_grps) +
  ggtitle("") + xlab('') + ylab('Losses (kAF/year)') +
  labs(tag = subfig[5]) +
  coord_cartesian(xlim=c(1.4,1.6), ylim=ylim_gainloss[,2])


######################
## now data split by season
#####################

### positive gains

df <- read.csv('figures/alluvial_season.csv', header=TRUE, sep=',',
               colClasses=c('character','character','numeric','numeric','character'))
df <- df[df$Sign == 1,]

### get months
df$Season <- factor(df$Season, levels=c('+Oct-Dec','+Jan-Mar','+Apr-Jun','+Jul-Sep'))

### order districts by total gain/loss
df$GainOrLoss = df$Magnitude * df$Sign
district_sum_gainloss = aggregate(df$Magnitude, by=list(District=df$District), FUN=sum)
district_sum_gainloss <- district_sum_gainloss[order(-district_sum_gainloss$x),]
district_order <- c('+F-1','+F-2','+F-3','+F-4','+F-5','+F-6','+F-7','+F-8','+F-9','+F-10',
                    '+F-11','+F-12','+F-13','+F-14','+F-15','+F-16',
                    '+O-1','+O-2','+O-3','+O-4','+O-5','+O-6','+O-7','+O-8','+O-9','+O-10',
                    '+O-11','+O-12','+O-13','+O-14','+O-15','+O-16','+O-17','+O-18','+O-19','+O-20',
                    '+O-21','+O-22','+O-23','+O-24','+O-25','+O-26','+O-27','+O-28','+O-29','+O-30',
                    '+O-31','+O-32','+O-33','+O-34','+O-35','+O-36','+O-37','+O-38','+O-39','+O-40')
df$District <- factor(df$District, levels = district_order)
df$District <- droplevels(df$District)
district_order <- levels(df$District)

### convert to long format (one row for each flow)
dflong <- to_lodes_form(df, key='WaterType', value='Group', id='Cohort', axes=c(1,2))

### get colors for columns
# group_colors <- rev(left_pal(4))
group_colors <- left_pal[1:4]
dflong_grps <- levels(dflong$Group)
district_sum_gainloss$color <- district_sum_gainloss$District
for (i in 1:length(district_sum_gainloss$District)){
  district_sum_gainloss$color[i] <- df$Color[df$District == district_sum_gainloss$District[i]][1]
}
district_colors <- district_sum_gainloss$color
for (i in 1:length(district_sum_gainloss$District)){
  d <- district_order[i]
  district_colors[i] <- district_sum_gainloss$color[district_sum_gainloss$District == d][1]
}
group_colors <- c(group_colors, district_colors)

### get labels for columns
dflong_label <- as.character(dflong$Group)
for (i in 1:length(dflong$Magnitude)){
  grp <- as.character(dflong$Group[i])
  grp_source <- sum(dflong$Magnitude[dflong$Group == grp])
  if (grp_source < label_threshold[6]){
    dflong_label[i] = ''
  }else{
    dflong_label[i] = substr(dflong_label[i],2,200)
  }
}
dflong$label = dflong_label


# plot with all strata colored
p6 <- ggplot(data = dflong,
             aes(x = WaterType, stratum = Group, alluvium = Cohort, y = Magnitude)) +
  theme_minimal(base_size= gg_font[2]) +
  theme(legend.position='none') +
  geom_alluvium(aes(fill=Group), alpha=0.8) +
  geom_stratum(aes(fill=Group), alpha=1) +
  geom_text(stat = "stratum", aes(label = label), size= label_font[2], color='white') +
  scale_fill_manual(values=group_colors, breaks=dflong_grps, labels=dflong_grps) +
  ggtitle("") + xlab('') + ylab('Gains (kAF/year)') +
  labs(tag = subfig[6]) +
  coord_cartesian(xlim=c(1.4,1.6), ylim=ylim_gainloss[,3])



### negative gains

df <- read.csv('figures/alluvial_season.csv', header=TRUE, sep=',',
               colClasses=c('character','character','numeric','numeric','character'))
df <- df[df$Sign == -1,]

### get months
df$Season <- factor(df$Season, levels=c('-Oct-Dec','-Jan-Mar','-Apr-Jun','-Jul-Sep'))

### order districts by total gain/loss
df$GainOrLoss = df$Magnitude * df$Sign
district_sum_gainloss = aggregate(df$Magnitude, by=list(District=df$District), FUN=sum)
district_sum_gainloss <- district_sum_gainloss[order(-district_sum_gainloss$x),]
district_order <- c('-F-1','-F-2','-F-3','-F-4','-F-5','-F-6','-F-7','-F-8','-F-9','-F-10',
                    '-F-11','-F-12','-F-13','-F-14','-F-15','-F-16',
                    '-O-1','-O-2','-O-3','-O-4','-O-5','-O-6','-O-7','-O-8','-O-9','-O-10',
                    '-O-11','-O-12','-O-13','-O-14','-O-15','-O-16','-O-17','-O-18','-O-19','-O-20',
                    '-O-21','-O-22','-O-23','-O-24','-O-25','-O-26','-O-27','-O-28','-O-29','-O-30',
                    '-O-31','-O-32','-O-33','-O-34','-O-35','-O-36','-O-37','-O-38','-O-39','-O-40')
df$District <- factor(df$District, levels = district_order)
df$District <- droplevels(df$District)
district_order <- levels(df$District)

### convert to long format (one row for each flow)
dflong <- to_lodes_form(df, key='WaterType', value='Group', id='Cohort', axes=c(1,2))

### get colors for columns
# group_colors <- rev(left_pal(4))
group_colors <- left_pal[1:4]
dflong_grps <- levels(dflong$Group)
district_sum_gainloss$color <- district_sum_gainloss$District
for (i in 1:length(district_sum_gainloss$District)){
  district_sum_gainloss$color[i] <- df$Color[df$District == district_sum_gainloss$District[i]][1]
}
district_colors <- district_sum_gainloss$color
for (i in 1:length(district_sum_gainloss$District)){
  d <- district_order[i]
  district_colors[i] <- district_sum_gainloss$color[district_sum_gainloss$District == d][1]
}
group_colors <- c(group_colors, district_colors)

### get labels for columns
dflong_label <- as.character(dflong$Group)
for (i in 1:length(dflong$Magnitude)){
  grp <- as.character(dflong$Group[i])
  grp_source <- sum(dflong$Magnitude[dflong$Group == grp])
  if (grp_source < label_threshold[7]){
    dflong_label[i] = ''
  }else{
    dflong_label[i] = substr(dflong_label[i],2,200)
  }
}
dflong$label = dflong_label


# plot with all strata colored
p7 <- ggplot(data = dflong,
             aes(x = WaterType, stratum = Group, alluvium = Cohort, y = Magnitude)) +
  theme_minimal(base_size= gg_font[2]) +
  theme(legend.position='none') +
  geom_alluvium(aes(fill=Group), alpha=0.8) +
  geom_stratum(aes(fill=Group), alpha=1) +
  geom_text(stat = "stratum", aes(label = label), size= label_font[2], color='white') +
  scale_fill_manual(values=group_colors, breaks=dflong_grps, labels=dflong_grps) +
  ggtitle("") + xlab('') + ylab('Losses (kAF/year)') +
  labs(tag = subfig[7]) +
  coord_cartesian(xlim=c(1.4,1.6), ylim=ylim_gainloss[,4])






######################
## now data split by wateryear type/wetness
#####################

### positive gains

df <- read.csv('figures/alluvial_wetness.csv', header=TRUE, sep=',',
               colClasses=c('character','character','numeric','numeric','character'))
df = df[df$Sign == 1,]

### get quartile
df$HydroQuartile <- factor(df$HydroQuartile, levels=c('+q1','+q2','+q3','+q4'))

### order districts by total gain/loss
df$GainOrLoss = df$Magnitude * df$Sign
district_sum_gainloss = aggregate(df$Magnitude, by=list(District=df$District), FUN=sum)
district_sum_gainloss <- district_sum_gainloss[order(-district_sum_gainloss$x),]
district_order <- c('+F-1','+F-2','+F-3','+F-4','+F-5','+F-6','+F-7','+F-8','+F-9','+F-10',
                    '+F-11','+F-12','+F-13','+F-14','+F-15','+F-16',
                    '+O-1','+O-2','+O-3','+O-4','+O-5','+O-6','+O-7','+O-8','+O-9','+O-10',
                    '+O-11','+O-12','+O-13','+O-14','+O-15','+O-16','+O-17','+O-18','+O-19','+O-20',
                    '+O-21','+O-22','+O-23','+O-24','+O-25','+O-26','+O-27','+O-28','+O-29','+O-30',
                    '+O-31','+O-32','+O-33','+O-34','+O-35','+O-36','+O-37','+O-38','+O-39','+O-40')
df$District <- factor(df$District, levels = district_order)
df$District <- droplevels(df$District)
district_order <- levels(df$District)

### convert to long format (one row for each flow)
dflong <- to_lodes_form(df, key='WaterType', value='Group', id='Cohort', axes=c(1,2))

### get colors for columns
# group_colors <- rev(left_pal(4))
group_colors <- left_pal[1:4]
dflong_grps <- levels(dflong$Group)
district_sum_gainloss$color <- district_sum_gainloss$District
for (i in 1:length(district_sum_gainloss$District)){
  district_sum_gainloss$color[i] <- df$Color[df$District == district_sum_gainloss$District[i]][1]
}
district_colors <- district_sum_gainloss$color
for (i in 1:length(district_sum_gainloss$District)){
  d <- district_order[i]
  district_colors[i] <- district_sum_gainloss$color[district_sum_gainloss$District == d][1]
}
group_colors <- c(group_colors, district_colors)

### get labels for columns
dflong_label <- as.character(dflong$Group)
for (i in 1:length(dflong$Magnitude)){
  grp <- as.character(dflong$Group[i])
  grp_source <- sum(dflong$Magnitude[dflong$Group == grp])
  if (grp_source < label_threshold[8]){
    dflong_label[i] = ''
  }else{
    dflong_label[i] = substr(dflong_label[i],2,200)
  }
}
dflong$label = dflong_label


# plot with all strata colored
p8 <- ggplot(data = dflong,
             aes(x = WaterType, stratum = Group, alluvium = Cohort, y = Magnitude)) +
  theme_minimal(base_size= gg_font[2]) +
  theme(legend.position='none') +
  geom_alluvium(aes(fill=Group), alpha=0.8) +
  geom_stratum(aes(fill=Group), alpha=1) +
  geom_text(stat = "stratum", aes(label = label), size= label_font[2], color='white') +
  scale_fill_manual(values=group_colors, breaks=dflong_grps, labels=dflong_grps) +
  ggtitle("") + xlab('') + ylab('Gains (kAF/year)') +
  labs(tag = subfig[8]) +
  coord_cartesian(xlim=c(1.4,1.6), ylim=ylim_gainloss[,5])


### negative gains

df <- read.csv('figures/alluvial_wetness.csv', header=TRUE, sep=',', colClasses=c('character','character','numeric','numeric','character'))
df = df[df$Sign == -1,]

### get quartile
df$HydroQuartile <- factor(df$HydroQuartile, levels=c('-q1','-q2','-q3','-q4'))

### order districts by total gain/loss
df$GainOrLoss = df$Magnitude * df$Sign
district_sum_gainloss = aggregate(df$Magnitude, by=list(District=df$District), FUN=sum)
district_sum_gainloss <- district_sum_gainloss[order(-district_sum_gainloss$x),]
district_order <- c('-F-1','-F-2','-F-3','-F-4','-F-5','-F-6','-F-7','-F-8','-F-9','-F-10',
                    '-F-11','-F-12','-F-13','-F-14','-F-15','-F-16',
                    '-O-1','-O-2','-O-3','-O-4','-O-5','-O-6','-O-7','-O-8','-O-9','-O-10',
                    '-O-11','-O-12','-O-13','-O-14','-O-15','-O-16','-O-17','-O-18','-O-19','-O-20',
                    '-O-21','-O-22','-O-23','-O-24','-O-25','-O-26','-O-27','-O-28','-O-29','-O-30',
                    '-O-31','-O-32','-O-33','-O-34','-O-35','-O-36','-O-37','-O-38','-O-39','-O-40')
df$District <- factor(df$District, levels = district_order)
df$District <- droplevels(df$District)
district_order <- levels(df$District)
### convert to long format (one row for each flow)
dflong <- to_lodes_form(df, key='WaterType', value='Group', id='Cohort', axes=c(1,2))

### get colors for columns
# group_colors <- rev(left_pal(4))
group_colors <- left_pal[1:4]
dflong_grps <- levels(dflong$Group)
district_sum_gainloss$color <- district_sum_gainloss$District
for (i in 1:length(district_sum_gainloss$District)){
  district_sum_gainloss$color[i] <- df$Color[df$District == district_sum_gainloss$District[i]][1]
}
district_colors <- district_sum_gainloss$color
for (i in 1:length(district_sum_gainloss$District)){
  d <- district_order[i]
  district_colors[i] <- district_sum_gainloss$color[district_sum_gainloss$District == d][1]
}
group_colors <- c(group_colors, district_colors)

### get labels for columns
dflong_label <- as.character(dflong$Group)
for (i in 1:length(dflong$Magnitude)){
  grp <- as.character(dflong$Group[i])
  grp_source <- sum(dflong$Magnitude[dflong$Group == grp])
  if (grp_source < label_threshold[9]){
    dflong_label[i] = ''
  }else{
    dflong_label[i] = substr(dflong_label[i],2,200)
  }
}
dflong$label = dflong_label


# plot with all strata colored
p9 <- ggplot(data = dflong,
             aes(x = WaterType, stratum = Group, alluvium = Cohort, y = Magnitude)) +
  theme_minimal(base_size= gg_font[2]) +
  theme(legend.position='none') +
  geom_alluvium(aes(fill=Group), alpha=0.8) +
  geom_stratum(aes(fill=Group), alpha=1) +
  geom_text(stat = "stratum", aes(label = label), size= label_font[2], color='white') +
  scale_fill_manual(values=group_colors, breaks=dflong_grps, labels=dflong_grps) +
  ggtitle("") + xlab('') + ylab('Losses (kAF/year)') +
  labs(tag = subfig[9]) +
  coord_cartesian(xlim=c(1.4,1.6), ylim=ylim_gainloss[,6])


if (run_mode == 2){
  g <- arrangeGrob(p4, p5, p6, p7, p8, p9, nrow=3, ncol=2)
  ggsave('figures/alluvia_gains.jpg', g, width=7, height=10, units='in', dpi=500)
}else{
  g <- arrangeGrob(p1, p4, p5, p2, p6, p7, p3, p8, p9, nrow=3, ncol=3)
  ggsave('figures/alluvia_combined.jpg', g, width=6, height=8, units='in', dpi=500)
}


