
AboveMIL = data.frame(matrix(vector(), 31, 100))
MIL = data.frame(matrix(vector(), 31, 100))
BelowMIL = data.frame(matrix(vector(), 31, 100))

for(i in 0:99){
  
  filename=paste0("../../calfews_src/data/MGHMM_synthetic/DailyQ_s",i,".csv")
  test=read.csv(filename)
  
  
  #Sum to annual 
  
  test_annual=aggregate(test,by = list(test$Year),FUN=sum)
  
  #Sum columns to three regions 
  
  AboveMIL[,i+1]=rowSums(test_annual[,6:15])
  MIL[,i+1]=test_annual[,16]
  BelowMIL[,i+1]=rowSums(test_annual[,17:20])
  
}

AboveMIL=AboveMIL*1.233e6*1e-12
MIL=MIL*1.233e6*1e-12
BelowMIL=BelowMIL*1.233e6*1e-12


write.csv(x = AboveMIL,file = "./mhmm_data/AboveMIL_TL.csv",row.names = FALSE)
write.csv(x = MIL,file = "./mhmm_data/MIL_TL.csv",row.names = FALSE)
write.csv(x = BelowMIL,file = "./mhmm_data/BelowMIL_TL.csv",row.names = FALSE)
