"""Generate the three manuscript figures from checked model outputs."""
from pathlib import Path
import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DEFAULT=Path(__file__).resolve().parents[1]/"results"


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--results",type=Path,default=DEFAULT)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    out=a.output or a.results/"figures"
    out.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"axes.labelsize":10,"svg.fonttype":"path","pdf.fonttype":42,"ps.fonttype":42,"axes.spines.top":False,"axes.spines.right":False})
    summary=pd.read_csv(a.results/"model_summary.csv")
    def get(model,contrast="episode_vs_reference"):
        rows=summary[(summary.model==model)&(summary.contrast==contrast)]
        assert len(rows)==1,(model,contrast)
        return rows.iloc[0]
    def save(fig,name):
        fig.savefig(out/(name+".svg"),bbox_inches="tight")
        fig.savefig(out/(name+".eps"),bbox_inches="tight")
        fig.savefig(out/(name+".pdf"),bbox_inches="tight")
        fig.savefig(out/(name+".png"),dpi=1200,bbox_inches="tight",facecolor="white")
        plt.close(fig)
    cities=pd.read_csv(a.results/"weather_adjusted_city_estimates.csv")
    order=sorted(cities.city.unique())+["Equal-city mean"]
    fig,ax=plt.subplots(figsize=(6.5,5.1),layout="constrained")
    for offset,contrast,color,label in [(-.13,"episode_vs_reference","#215A80","Episode vs neither"),(.13,"episode_vs_wind_only","#B75826","Episode vs low wind only")]:
        rows=cities[cities.contrast==contrast].set_index("city").reindex(order[:-1])
        points=list(rows.estimate_ppb)+[get("weather_adjusted",contrast).estimate_ppb]
        lower=list(rows.ci_lower)+[get("weather_adjusted",contrast).ci_lower]
        upper=list(rows.ci_upper)+[get("weather_adjusted",contrast).ci_upper]
        ypos=np.arange(len(order))+offset
        ax.hlines(ypos,lower,upper,color=color,lw=1.1)
        ax.scatter(points,ypos,c=color,s=18,marker="o" if offset<0 else "s",label=label,zorder=4)
    ax.set_yticks(np.arange(len(order)),order)
    ax.invert_yaxis(); ax.axvline(0,color="0.4",lw=.8,ls="--")
    ax.axhline(len(order)-1.5,color="0.82",lw=.6)
    ax.set_xlabel("Adjusted NO₂ difference (ppb)")
    ax.legend(loc="upper center",bbox_to_anchor=(.5,1.09),ncol=2,frameon=False,fontsize=8)
    ax.grid(axis="x",alpha=.15)
    save(fig,"Fig1_city_contrasts")
    models=[("calendar_only","Calendar only"),("weather_adjusted","Weather adjusted"),("direct_calendar_support","Direct calendar support"),("core_monitors","Core monitors"),("equal_station_weights","Equal monitor weights"),("all_consecutive_episodes","All consecutive episodes"),("exclude_2020","Excluding 2020"),("city_median","City daily median")]
    fig,ax=plt.subplots(figsize=(6.5,3.9),layout="constrained")
    for y,(model,label) in enumerate(models):
        r=get(model); color="#215A80" if model=="weather_adjusted" else "#557E83"
        ax.hlines(y,r.ci_lower,r.ci_upper,color=color,lw=1.6)
        ax.scatter(r.estimate_ppb,y,c=color,s=30 if model=="weather_adjusted" else 20,zorder=4)
    ax.set_yticks(range(len(models)),[label for _,label in models]); ax.invert_yaxis()
    ax.axvline(0,color="0.4",lw=.8,ls="--");ax.grid(axis="x",alpha=.15)
    ax.set_xlabel("Episode vs neither-threshold days (ppb)")
    save(fig,"Fig2_sensitivity")
    phases=[("pre1_6_vs_reference","Days −6 to −1"),("episode_vs_reference","Episode"),("post1_2_vs_reference","Days 1–2 after"),("post3_6_vs_reference","Days 3–6 after")]
    fig,ax=plt.subplots(figsize=(6.5,3.7),layout="constrained")
    for offset,model,color,label in [(-.09,"phase_calendar","#889294","Calendar only"),(.09,"phase_adjusted","#215A80","Weather adjusted")]:
        for i,(contrast,_) in enumerate(phases):
            r=get(model,contrast)
            ax.vlines(i+offset,r.ci_lower,r.ci_upper,color=color,lw=1.4)
            ax.scatter(i+offset,r.estimate_ppb,c=color,s=25,marker="o" if offset<0 else "s",label=label if i==0 else None,zorder=4)
    ax.axhline(0,color="0.4",ls="--",lw=.8)
    ax.set_xticks(range(len(phases)),[label for _,label in phases])
    ax.set_ylabel("Difference from background days (ppb)")
    ax.legend(frameon=False,loc="best",fontsize=8)
    ax.grid(axis="y",alpha=.15)
    save(fig,"Fig3_episode_phases")
    print(out)


if __name__=="__main__":
    main()
