include(joinpath(@__DIR__, "plot_utils.jl"))

using PythonCall
using JSON, DataFrames
using Printf

function figure_3_data()
    data = JSON.parsefile(joinpath(@__DIR__, "../results/repeated_bell/decoder=mle.json"))
    N = length(data)
    ps = [data[i]["noise_spec"]["p"] for i = 1:N]
    ds = [data[i]["d"] for i = 1:N]
    nss = [data[i]["num_samples"] for i = 1:N]
    nhfs_no_flip = [data[i]["num_dgs"] for i = 1:N]
    nhfs = [data[i]["num_hfs"][end] for i = 1:N]
    nles = [data[i]["num_oes"] for i = 1:N]
    nes = [data[i]["num_les"] for i = 1:N]
    df = DataFrame(Dict(
        "p" => ps,
        "d" => ds,
        "num_samples" => nss,
        "num_heralded_failures_no_flip" => nhfs_no_flip,
        "num_heralded_failures" => nhfs,
        "num_logical_errors" => nles,
        "num_total_errors" => nes
    ))
    df = filter(row -> row[:num_samples] > 100, df)
    sort!(df, :p)
    return df
end

figure_3_data()

function figure_3_threshold()
    ax, fig = generate_fig(;
        legend_font_size,
        xtick_label_size = axes_font_size, ytick_label_size = axes_font_size,
        axes_label_size = axes_font_size,
        font_size = axes_font_size,
        figsize = ((3 + 3 / 8) / 2, 1.9)
    )
    df = figure_3_data()
    unique_ds = sort(unique(df[!, :d]))
    base_color = "orange"
    colors = ["#DCE5EF", "#C7D8E2", "#8EA5B8", "#718CA3", "#54748D"]
    markers = ["o"]

    xs_lines = Vector{Float64}[]
    nes_lines = Vector{Int}[]
    nss_lines = Vector{Int}[]
    for d in unique_ds
        df_line = df[df[!, :d] .== d, :]
        push!(xs_lines, df_line[!, :p])
        push!(nes_lines, df_line[!, :num_total_errors])
        push!(nss_lines, df_line[!, :num_samples])
    end
    lines = [ResultLine(xs_line, nes_line, nss_line) for (xs_line, nes_line, nss_line) in zip(xs_lines, nes_lines, nss_lines)]
    plot_ler_with_error_bar!(ax, lines, ["$d" for d in unique_ds]; 
        colors = colors,
        markers = markers, markersize,
        linewidth, markeredgewidth,
        markerfacecolors = colors,
        markeredgecolors = ["#C7D8E2", "#8EA5B8", "#718CA3", "#55748E", "#475F73"],
        alphas = [1.0],
        xlabel="Physical error rate", ylabel="Logical error rate", 
        ylim_min = 6e-6,
        xscale = "log",

        legend_loc = "lower right", bbox_to_anchor = (1.02, 0.45),
        legend_handletextpad = 0.3, legend_handlelength = 1.2,
        legend_labelspacing = 0.2, 

        subplot_left = 0.25, subplot_right = 0.95, 
        subplot_bottom = 0.15, subplot_top = 0.95,
    )
    plt.savefig(joinpath(@__DIR__, "../figs/fig_3_threshold.pdf"))
    return fig
end

function figure_3_suppression()
    df = figure_3_data()
    df = filter(row -> row[:p] in [10^(-3+0.05*i) for i = 4:4:12], df)
    sort!(df, :d)
    grouped_lines = Dict{Symbol, Dict{Float64, ResultLine}}()
    ps = sort(unique(df[!, :p]))
    for rk in ps
        df_line = filter(r -> r[:p] == rk, df)
        for ck in (:num_heralded_failures, :num_heralded_failures_no_flip)
            haskey(grouped_lines, ck) || (grouped_lines[ck] = Dict{Float64, ResultLine}())
            xs = df_line[!, :d]
            nes = df_line[!, ck]
            nss = df_line[!, :num_samples]
            line = ResultLine(xs, nes, nss)
            grouped_lines[ck][rk] = line
        end
    end

    color_map = (rk, ck) -> begin
        colors = if ck === :num_heralded_failures
            reverse(["#DCE5EF", "#C7D8E2", "#8EA5B8", "#718CA3", "#54748D"])
        else
            (["#9D4561", "#B45370", "#C77F96", "#DAAAB9"])
        end
        return colors[searchsortedfirst(ps, rk)]
    end
    markeredgecolor_map = (rk, ck) -> begin
        colors = if ck === :num_heralded_failures
            reverse(["#C7D8E2", "#8EA5B8", "#718CA3", "#55748E", "#475F73"])
        else
            (["#813950", "#9D4561", "#B45370", "#C77F96"])
        end
        return colors[searchsortedfirst(ps, rk)]
    end
    markerfacecolor_map = color_map

    ax, fig = generate_fig(; 
        legend_font_size,
        xtick_label_size = axes_font_size, ytick_label_size = axes_font_size,
        axes_label_size = axes_font_size,
        font_size = axes_font_size,
        figsize = ((3 + 3 / 8) / 2, 1.9)
    )
    plot_groups_with_error_bar!(ax, grouped_lines; 
        xlabel="Code distance", ylabel="Heralded failure rate",
        xscale="linear", yscale="log",
        xlim_min = 3e-5, xlim_max = nothing, ylim_min = 1e-5, ylim_max = nothing,
        xticks = [3, 5, 7, 9, 11],
        column_labels = Dict(
            :num_heralded_failures_no_flip => "First\nstep",
            :num_heralded_failures => "Both\nsteps",
        ),
        row_labels = Dict(p => @sprintf("%.2f", p*100)*"%" for p in ps),
        row_title = "\n    p",

        # marker_map = , 
        color_map, 
        markeredgecolor_map,
        markerfacecolor_map,

        # line styles
        linewidth, markersize, markeredgewidth,
        errorbar_capsize=nothing,

        legend_handletextpad = -1.5, legend_handlelength = 1.2,
        legend_columnspacing = 0.5, legend_labelspacing = 0.2, 
        legend_borderpad = 0.0,
        legend_loc = "lower left",
        bbox_to_anchor = (0.01, -0.005),
        rev_row_keys = true,

        subplot_left = 0.25, subplot_right = 0.95, 
        subplot_bottom = 0.15, subplot_top = 0.95,
    )
    plt.savefig(joinpath(@__DIR__, "../figs/fig_3_suppression.pdf"))
    return fig
end

function figure_3_ghz()
    py_str = read(joinpath(@__DIR__, "../scripts/figure_3_ghz.py"), String)
    pyexec(py_str, Main)
end

linewidth=0.75
markersize = 3.0
markeredgewidth=0.5
axes_font_size = 7
legend_font_size = 5
figure_3_threshold()
figure_3_suppression()
figure_3_ghz()