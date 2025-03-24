using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
/// <summary>
/// 面板管理器，用栈来存储UI
/// </summary>
public class PanelManager
{
    /// <summary>
    /// 存储UI面板的栈
    /// </summary>
    private Stack<BasePanel> stackPanel;
    /// <summary>
    /// UI管理器
    /// </summary>
    private UIManager uiManager;
    private BasePanel panel;

    public PanelManager()
    {
        stackPanel = new Stack<BasePanel>();
        uiManager = new UIManager();
    }
    /// <summary>
    /// UI的入栈操作，此操作会显示一个面板
    /// </summary>
    /// <param name="nextPanel">要显示的面板</param>
    public void Push(BasePanel nextPanel)
    {
        if (stackPanel.Count > 0) 
        {
            panel = stackPanel.Peek();
            panel.OnPause();
        }
        stackPanel.Push(nextPanel);
        GameObject panelGameObject = uiManager.GetSingleUI(nextPanel.UIType);
        //把所有对象的初始透明度变成0
        if(panelGameObject.GetComponent<Image>())
            panelGameObject.GetComponent<Image>().color = new Color(panelGameObject.GetComponent<Image>().color.r, panelGameObject.GetComponent<Image>().color.g, panelGameObject.GetComponent<Image>().color.b, 0);
        foreach(Transform child in panelGameObject.transform)
        {
            if(child.GetComponent<Image>())
                child.GetComponent<Image>().color = new Color(child.GetComponent<Image>().color.r, child.GetComponent<Image>().color.g, child.GetComponent<Image>().color.b, 0);
        }
        nextPanel.Initialize(new UITool(panelGameObject));
        nextPanel.Initialize(this);
        nextPanel.Initialize(uiManager);
        nextPanel.OnEnter();
    }
    /// <summary>
    /// UI的出栈操作，此操作会执行面板的OnExit方法
    /// </summary>
    /// <param name="nextPanel">要显示的面板</param>
    public void Pop()
    {
        if (stackPanel.Count > 0)
        {
            stackPanel.Peek().OnExit();
            stackPanel.Pop();
        }

        if (stackPanel.Count > 0)
            stackPanel.Peek().OnResume();
    }
    /// <summary>
    /// 执行所有面板的OnExit()
    /// </summary>
    public void PopAll()
    {
        while (stackPanel.Count > 0)
        {
            stackPanel.Peek().OnExit();
            stackPanel.Pop();
        }
    }
}
