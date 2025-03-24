using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// 所有UI面板的父类，包含UI面板的状态信息
/// </summary>
public abstract class BasePanel
{
    /// <summary>
    /// UI信息
    /// </summary>
    public UIType UIType { get; private set; }
    /// <summary>
    /// UI管理工具
    /// </summary>
    public UITool UITool { get; private set; }
    /// <summary>
    /// 面板管理器
    /// </summary>
    public PanelManager PanelManager { get; private set; }
    /// <summary>
    /// UI管理器
    /// </summary>
    public UIManager UIManager { get; private set; }
    /// <summary>
    /// 初始化UITool
    /// </summary>
    /// <param name="tool"></param>
    public void Initialize(UITool tool)
    {
        UITool = tool;
    }
    /// <summary>
    /// 初始化面板管理器
    /// </summary>
    /// <param name="tool"></param>
    public void Initialize(PanelManager panelManager)
    {
        PanelManager = panelManager;
    }
    /// <summary>
    /// 初始化UI管理器
    /// </summary>
    /// <param name="tool"></param>
    public void Initialize(UIManager uiManager)
    {
        UIManager = uiManager;
    }
    public BasePanel(UIType uiType)
    {
        UIType = uiType;
    }
    /// <summary>
    /// UI进入时执行的操作，只会执行一次
    /// </summary>
    public virtual void OnEnter() { }
    /// <summary>
    /// UI暂停时执行的操作
    /// </summary>
    public virtual void OnPause()
    {
        UITool.GetOrAddComponent<CanvasGroup>().blocksRaycasts = false;
    }
    /// <summary>
    /// UI继续时执行的操作
    /// </summary>
    public virtual void OnResume()
    {
        UITool.GetOrAddComponent<CanvasGroup>().blocksRaycasts = true;
    }
    /// <summary>
    /// UI退出时执行的操作
    /// </summary>
    public virtual void OnExit()
    {
        UIManager.DestroyUI(UIType);
    }
    
}
