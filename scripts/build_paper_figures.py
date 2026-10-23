"""Publication figures from stored measurements, not illustrative accuracy values."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/paper/figures'
OUT.mkdir(parents=True, exist_ok=True)
active = json.loads((ROOT/'reports/final_metrics.json').read_text())
candidate = json.loads((ROOT/'reports/accuracy_target_experiment.json').read_text())
audit = json.loads((ROOT/'reports/training_audit.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,
                     'axes.spines.right':False,'axes.titleweight':'bold','axes.labelcolor':'#263d50',
                     'text.color':'#173952','svg.fonttype':'none'})
blue,cyan,orange = '#235d87','#439ca9','#c87634'


def save(fig,name):
    fig.savefig(OUT/(name+'.png'),dpi=240,bbox_inches='tight',facecolor='white')
    fig.savefig(OUT/(name+'.svg'),bbox_inches='tight',facecolor='white')
    plt.close(fig)


def box(ax,x,y,w,h,text,color='#e9f1f7'):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.02,rounding_size=0.06',
                              edgecolor=blue,facecolor=color,linewidth=1.2))
    ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=11)


def arrow(ax,a,b,label=None):
    ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='->',lw=1.6,color=blue))
    if label: ax.text((a[0]+b[0])/2,(a[1]+b[1])/2+.1,label,ha='center',fontsize=9)


fig,ax=plt.subplots(figsize=(10,4.2));ax.set(xlim=(0,10),ylim=(0,4.2));ax.axis('off')
box(ax,.2,2.5,2.1,1,'Browser interface\nScan / review / export')
box(ax,3.1,2.5,2.6,1,'Local FastAPI boundary\nOrigin / host / size checks')
box(ax,6.6,2.5,3.1,1,'Public YouTube API\nChannel / video comments')
arrow(ax,(2.3,3),(3.1,3));arrow(ax,(5.7,3),(6.6,3))
box(ax,3.1,.5,2.6,1,'Validated text input\nSelected local ML artifact')
box(ax,6.6,.5,3.1,1,'SQLite evidence + audit\nHuman review decisions')
arrow(ax,(4.4,2.5),(4.4,1.5));arrow(ax,(5.7,1),(6.6,1))
ax.text(.3,.8,'Local inference by default\nExternal explanations: opt-in',fontsize=10)
ax.text(5,4,'SYSTEM ARCHITECTURE',ha='center',fontsize=14,weight='bold')
save(fig,'01_architecture')

fig,ax=plt.subplots(figsize=(10,3.7));ax.set(xlim=(0,10),ylim=(0,3.7));ax.axis('off')
for x,text in [(0.15,'Collect distinct\npublic comments'),(2.65,'AI flags\nNot a verdict'),(5.15,'Human reads\nand confirms'),(7.65,'Record channel-\nscoped evidence')]:box(ax,x,2.05,2.15,.85,text)
for x in [2.3,4.8,7.3]:arrow(ax,(x,2.475),(x+.35,2.475))
box(ax,5.15,.3,4.65,.95,'3 confirmed harms: repeated pattern\nVerify owner authorization\nConfirm the external action','#e6f2ed')
arrow(ax,(8.7,2.05),(8.7,1.25))
ax.text(.2,.65,'Rescans do not add strikes.\nChanged text resets review.\nNo automatic warnings or account suspensions.',fontsize=10)
ax.text(5,3.4,'HUMAN-SUPERVISED MODERATION',ha='center',fontsize=14,weight='bold')
save(fig,'02_review_workflow')

fig,axes=plt.subplots(1,2,figsize=(10,3.5),layout='constrained')
splits=audit['splits'];names=['train','validation','test'];values=[splits[n] for n in names]
bars=axes[0].bar(['Training','Validation','Test'],values,color=[blue,cyan,'#879eaf'])
axes[0].bar_label(bars,labels=[f'{v:,}' for v in values],padding=4);axes[0].set_ylim(0,79000)
axes[0].set_title('Retained examples by split');axes[0].set_ylabel('Examples')
labels=list(audit['positive_training_support']);supported=[k for k in labels if audit['positive_training_support'][k]>0]
bars=axes[1].barh(supported,[audit['positive_training_support'][k] for k in supported],color=[orange,blue])
axes[1].bar_label(bars,labels=[f"{audit['positive_training_support'][k]:,}" for k in supported],padding=4)
axes[1].set_xlim(0,29000);axes[1].set_title('Positive training supervision');axes[1].set_xlabel('Examples (six other categories: 0)')
save(fig,'03_data_coverage')

fig,ax=plt.subplots(figsize=(10,4.1),layout='constrained')
metrics=['accuracy','precision','recall','f1'];x=np.arange(4)
for offset,record,color,label in [(-.19,active['binary'],blue,'Serving hybrid SVM'),(.19,candidate['test_evaluation'],cyan,'Binary research candidate')]:
    values=[record[k]*100 for k in metrics];bars=ax.bar(x+offset,values,.36,label=label,color=color)
    ax.bar_label(bars,labels=[f'{v:.2f}' for v in values],padding=4,fontsize=10,bbox=dict(facecolor='white',edgecolor='none',pad=.5))
ax.set_xticks(x,['Accuracy','Precision','Recall','F1']);ax.set_ylim(0,108);ax.set_ylabel('Test score (%)')
ax.legend(loc='lower left',frameon=True,facecolor='white',framealpha=1);ax.set_title('Held-out binary results | 14,318 examples')
ax.axhline(96,color=orange,linestyle='--',lw=1);ax.text(3.55,98.2,'96% target',ha='right',fontsize=9,color=orange)
save(fig,'04_test_comparison')

fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
for ax,record,title in zip(axes,[active['binary'],candidate['test_evaluation']],['Serving hybrid SVM','Binary research candidate']):
    matrix=np.asarray(record['confusion_matrix']);assert matrix.sum()==14318
    ax.imshow(matrix,cmap='Blues',vmin=0,vmax=9500)
    for (r,c),value in np.ndenumerate(matrix):ax.text(c,r,f'{value:,}',ha='center',va='center',fontsize=16,color='white' if value>5000 else '#173952')
    ax.set_xticks([0,1],['Safe','Harmful']);ax.set_yticks([0,1],['Safe','Harmful'])
    ax.set_xlabel('Predicted label');ax.set_ylabel('Observed label');ax.set_title(title)
save(fig,'05_confusion_matrices')

fig,ax=plt.subplots(figsize=(10,3.2),layout='constrained')
per=active['test']['per_class'];keys=active['test']['selection_labels'];vals=[per[k]['f1']*100 for k in keys]
bars=ax.barh(keys,vals,color=[orange,blue]);ax.bar_label(bars,labels=[f'{v:.2f}%' for v in vals],padding=5)
ax.set_xlim(0,105);ax.set_xlabel('Held-out F1 (%)');ax.set_title('Serving model: evaluated category performance')
ax.text(.99,.04,'Six unsupported categories are omitted, not scored as successful.',transform=ax.transAxes,ha='right',fontsize=9)
save(fig,'06_category_f1')
print('Saved six figures as PNG and SVG in',OUT)
