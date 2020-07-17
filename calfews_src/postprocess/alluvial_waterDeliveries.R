### script for alluvial plots visualizing district_grp/bank deliveries
library('ggalluvial')
library('viridis')

folder1 = 'FKC_capacity_wy2017'
wy1 = 2011

folder2 = 'FKC_capacity_wy2017__LWT_inleiubank_DLESSJSFW_0'
wy2 = 2011



df <- read.csv(file=paste('C:/Users/Andrew/PycharmProjects/ORCA_COMBINED/calfews_src/data/results/',folder1,'/district_reorg.csv', sep=''), header=TRUE, sep=",", stringsAsFactors = F)

df_wy1 <- df[(df$Wateryear==wy1),c(1,2,3,4,5)]
df_wy1$dataset <- toString(wy1)

df_wy1 <- df_wy1[((df_wy1$District=='LWT')|(df_wy1$District=='DLE')|(df_wy1$District=='SSJ')|(df_wy1$District=='SFW')),]
# df_wy1 <- df_wy1[((df_wy1$District=='LWT')|(df_wy1$District=='ARV')),]
df_wy1 <- df_wy1[order(df_wy1$Axis, df_wy1$Label, df_wy1$District),]

# df_wy1$District_grp <- 'SID'
# df_wy1$District_grp[df_wy1$District=='LWT'] = 'LWT'
# df_wy1$Label_grp = df_wy1$Label
# df_wy1$Label_grp[(df_wy1$Label=='KRT')|(df_wy1$Label=='DLE')|(df_wy1$Label=='SSJ')|(df_wy1$Label=='SFW')] = 'SID'

# df_wy1$District_grp <- factor(df_wy1$District_grp, levels=c('LWT','SID'))
# df_wy1$Label_grp <- factor(df_wy1$Label_grp, levels=c('Pumping','Recovered_in','Banked_in','OtherSW','Friant','LWT','SID','Recovered_out','Banked_out','Recharged','Irrigation'))

df_wy1$District <- factor(df_wy1$District, levels=c('LWT','DLE','SSJ','SFW'))
# df_wy1$District <- factor(df_wy1$District, levels=c('LWT','ARV'))
df_wy1$Label <- factor(df_wy1$Label, levels=c('Pumping','Recoverey','Banked_in','OtherSW','Friant','LWT','DLE','SSJ','SFW','Recovered_out','Banking','Recharge','Irrigation'))
# df_wy1$Label <- factor(df_wy1$Label, levels=c('Pumping','Recovered_in','Banked_in','OtherSW','Friant','LWT','ARV','Recovered_out','Banked_out','Recharged','Irrigation'))
df_wy1$Axis <- factor(df_wy1$Axis, levels=c('Source','District','Use'))

df_wy1$dataset <- 1



df <- read.csv(file=paste('C:/Users/Andrew/PycharmProjects/ORCA_COMBINED/calfews_src/data/results/',folder2,'/district_reorg.csv', sep=''), header=TRUE, sep=",", stringsAsFactors = F)

df_wy2 <- df[(df$Wateryear==wy2),c(1,2,3,4,5)]
df_wy2$dataset <- toString(wy2)

df_wy2 <- df_wy2[((df_wy2$District=='LWT')|(df_wy2$District=='DLE')|(df_wy2$District=='SSJ')|(df_wy2$District=='SFW')),]
# df_wy2 <- df_wy2[((df_wy2$District=='LWT')|(df_wy2$District=='ARV')),]
df_wy2 <- df_wy2[order(df_wy2$Axis, df_wy2$Label, df_wy2$District),]

# df_wy2$District_grp <- 'SID'
# df_wy2$District_grp[df_wy2$District=='LWT'] = 'LWT'
# df_wy2$Label_grp = df_wy2$Label
# df_wy2$Label_grp[(df_wy2$Label=='KRT')|(df_wy2$Label=='DLE')|(df_wy2$Label=='SSJ')|(df_wy2$Label=='SFW')] = 'SID'

# df_wy2$District_grp <- factor(df_wy2$District_grp, levels=c('LWT','SID'))
# df_wy2$Label_grp <- factor(df_wy2$Label_grp, levels=c('Pumping','Recovered_in','Banked_in','OtherSW','Friant','LWT','SID','Recovered_out','Banked_out','Recharged','Irrigation'))

df_wy2$District <- factor(df_wy2$District, levels=c('LWT','DLE','SSJ','SFW'))
# df_wy2$District <- factor(df_wy2$District, levels=c('LWT','ARV'))
df_wy2$Label <- factor(df_wy2$Label, levels=c('Pumping','Recovery','Banked_in','OtherSW','Friant','LWT','DLE','SSJ','SFW','Recovered_out','Banking','Recharge','Irrigation'))
# df_wy2$Label <- factor(df_wy2$Label, levels=c('Pumping','Recovered_in','Banked_in','OtherSW','Friant','LWT','ARV','Recovered_out','Banked_out','Recharged','Irrigation'))
df_wy2$Axis <- factor(df_wy2$Axis, levels=c('Source','District','Use'))

df_wy2$dataset <- 2



df_wy3 = rbind(df_wy1, df_wy2)

pdf(file=paste('../figs/alluvial_',wy1,'_',folder1,'___',wy2,'_',folder2,'.pdf',sep=''), width=14, height=7)
ggplot(data = df_wy3,
    aes(x = Axis, stratum = Label, alluvium = Obs, y = Volume)) +
    scale_x_discrete(expand = c(.1, .05)) +
    geom_alluvium(aes(fill = District)) + scale_fill_viridis(discrete=T) +
    geom_stratum() +
    # geom_text(stat = "stratum", label.strata = T) +
    theme_minimal(base_size=20) + ylab('Water volume (tAF/yr)') + 
    guides(fill=guide_legend(title=NULL)) + facet_wrap(~ dataset, scales = "fixed")
dev.off()



