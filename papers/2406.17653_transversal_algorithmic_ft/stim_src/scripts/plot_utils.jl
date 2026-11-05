using PythonCall
import PythonPlot.pyplot as plt
import PythonPlot.matplotlib as matplotlib
using HypothesisTests: BinomialTest, confint
using Colors

export s_factory_output_fidelity, 
    plt, ResultLine, plot_groups_with_error_bar!, shade_color

function s_factory_output_fidelity(p)
    undet_error_rate = 7*p^3*(1-p)^4 + p^7
    post_select_rate = undet_error_rate + (1-p)^7 + 7*p^4*(1-p)^3
    return undet_error_rate / post_select_rate, post_select_rate
end

# Function to create shaded color
function shade_color(color_str::String, shade_factor::Float64)
    @assert -1 <= shade_factor <= 1
    # Parse the color string to a Colorant
    base_color = parse(Colorant, color_str)
    
    # Calculate the shaded color
    # If shade_factor is 0, return the original color
    # If shade_factor is 1, return black
    # If shade_factor is -1, return white
    shaded_color = if shade_factor > 0 
        weighted_color_mean(shade_factor, colorant"black", base_color)
    else
        weighted_color_mean(-shade_factor, colorant"white", base_color)
    end
    
    # Return the shaded color as a hex string
    r = shaded_color
    return "#$(hex(r))"
end

struct ResultLine
    xs::Vector{<:Real}
    ys::Vector{<:Real}
    xerrs::Matrix{<:Real}
    yerrs::Matrix{<:Real}
    function ResultLine(xs::Vector{<:Real}, ys::Vector{<:Real}; xerrs::Matrix{<:Real} = zeros(2, length(xs)), yerrs::Matrix{<:Real} = zeros(2, length(ys)))
        @assert length(xs) == length(ys) == size(xerrs, 2) == size(yerrs, 2)
        @assert size(xerrs, 1) == size(yerrs, 1) == 2
        return new(xs, ys, xerrs, yerrs)
    end
end

function ResultLine(xs::Vector{<:Real}, y_nes::Vector{<:Real}, y_nss::Vector{<:Real})
    @assert length(xs) == length(y_nes) == length(y_nss)
    ys = y_nes ./ y_nss
    yerrs = [confint(BinomialTest(y_nes[i], y_nss[i]))[j] for j in 1:2, i in 1:length(y_nss)]
    yerrs[1, :] = ys - yerrs[1, :]
    yerrs[2, :] = yerrs[2, :] - ys
    return ResultLine(xs, ys; yerrs)
end

function ResultLine(x_nes::Vector{<:Real}, x_nss::Vector{<:Real}, y_nes::Vector{<:Real}, y_nss::Vector{<:Real})
    @assert length(x_nes) == length(x_nss) == length(y_nes) == length(y_nss)
    xs = x_nes ./ x_nss
    ys = y_nes ./ y_nss
    xerrs = [confint(BinomialTest(x_nes[i], x_nss[i]))[j] for j in 1:2, i in 1:length(x_nss)]
    xerrs[1, :] = xs - xerrs[1, :]
    xerrs[2, :] = xerrs[2, :] - xs
    yerrs = [confint(BinomialTest(y_nes[i], y_nss[i]))[j] for j in 1:2, i in 1:length(y_nss)]
    yerrs[1, :] = ys - yerrs[1, :]
    yerrs[2, :] = yerrs[2, :] - ys
    return ResultLine(xs, ys; xerrs, yerrs)
end

function plot_line_with_error_bar!(ax, line::ResultLine;
        label=nothing,
        color=nothing, alpha=nothing,
        marker=nothing, markersize=nothing,
        linewidth=nothing, markeredgewidth=nothing,
        markerfacecolor=nothing, markeredgecolor=nothing)
    xs = line.xs
    ys = line.ys
    xerr = line.xerrs
    yerr = line.yerrs
    ax.errorbar(xs, ys;
        xerr, yerr,
        label, 
        marker, markersize, 
        linewidth, markeredgewidth,
        markerfacecolor, markeredgecolor, 
        color, alpha)
    return ax
end

const DEFAULT_MARKERS = ["o"]
const DEFAULT_COLORS = ["#E5B887", "#A9C6D8", "b", "g", "r", "c", "m", "y", "k", "w"]
const DEFAULT_MARKERFACECOLORS = ["#FEEACF", "#E4F2FC", "b", "g", "r", "c", "m", "y", "k", "w"]
const DEFAULT_MARKEREDGECOLORS = ["#E5B887", "#A9C6D8", "b", "g", "r", "c", "m", "y", "k", "w"]

function generate_fig(; usetex::Bool = false, 
        legend_font_size = 8,
        xtick_label_size = 8, ytick_label_size = 8,
        axes_label_size = 10,
        font_size = 10,
        figsize = (4, 6))
    tex_fonts = Dict(
        # Use LaTeX to write all text
        "text.usetex"=> usetex,
        "font.family"=> "sans-serif",  # Helvetica Neue",
        "font.sans-serif"=> "Helvetica",
        # Use 10pt font in plots, to match 10pt font in document
        "axes.labelsize"=> axes_label_size,
        "font.size"=> font_size,
        # Make the legend/label fonts a little smaller
        "legend.fontsize"=> legend_font_size,
        "xtick.labelsize"=> xtick_label_size,
        "ytick.labelsize"=> ytick_label_size,
    )

    plt.rcParams.update(tex_fonts)
    fig, ax = plt.subplots(1, 1; sharey=true, sharex=true, figsize)
    return ax, fig
end

function plot_ler_with_error_bar(lines::Vector{ResultLine}, labels::Vector{<:Union{Nothing, String}};

        # line styles
        markers = DEFAULT_MARKERS,
        markerfacecolors = DEFAULT_MARKERFACECOLORS,
        markeredgecolors = DEFAULT_MARKEREDGECOLORS,
        colors = DEFAULT_COLORS,
        alphas = ones(length(lines)),

        # x and y axis
        xlabel::String = "Code distance", ylabel::String = "Logical error rate",
        xscale::String = "linear", yscale::String = "log",
        xlim_min = nothing, xlim_max = nothing, ylim_min = nothing, ylim_max = nothing,

        # legend settings
        legend_loc = "lower right",
        
        # font settings
        usetex::Bool = false, 
        legend_font_size = 8,
        xtick_label_size = 8, ytick_label_size = 8,
        axes_label_size = 10,
        font_size = 10,

        # figure settings
        figsize = (4, 6))
    ax, fig = generate_fig(; usetex, legend_font_size, xtick_label_size, ytick_label_size, axes_label_size, font_size, figsize)
    plot_ler_with_error_bar!(ax, lines, labels; 
        markers, markerfacecolors, markeredgecolors, colors, alphas,
        xlabel, ylabel, xscale, yscale, xlim_min, xlim_max, ylim_min, ylim_max,
        legend_loc)
    return ax, fig
end

function plot_ler_with_error_bar!(ax, lines::Vector{ResultLine}, labels::Vector{<:Union{Nothing, String}};
        # line styles
        markers = DEFAULT_MARKERS,
        linewidth=0.75,
        markersize=6,
        markeredgewidth=0.75,
        colors = DEFAULT_COLORS,
        markerfacecolors = colors,
        markeredgecolors = colors,
        alphas = ones(length(lines)),

        # x and y axis
        xlabel::String = "Code distance", ylabel::String = "Logical error rate",
        xscale::String = "linear", yscale::String = "log",
        xlim_min = nothing, xlim_max = nothing, ylim_min = nothing, ylim_max = nothing,
        xticks = nothing, yticks = nothing,

        # legend settings
        legend_loc = "lower right", bbox_to_anchor = nothing,
        legend_handlelength=1.0, legend_handletextpad=0.5,
        legend_labelspacing = 0.2, legend_borderpad=0.0,
        
        # subplot settings
        subplot_left=nothing, subplot_right=nothing, 
        subplot_top=nothing, subplot_bottom=nothing)

    for (i, (line, label)) in enumerate(zip(lines, labels))
        marker = markers[(i-1) % length(markers) + 1]
        markerfacecolor = markerfacecolors[(i-1) % length(markerfacecolors) + 1]
        markeredgecolor = markeredgecolors[(i-1) % length(markeredgecolors) + 1]
        color = colors[(i-1) % length(colors) + 1]
        alpha = alphas[(i-1) % length(alphas) + 1]
        plot_line_with_error_bar!(ax, line; 
            label,
            color, alpha,
            marker, markersize,
            linewidth, markeredgewidth,
            markerfacecolor, markeredgecolor)
    end

    ax.set_xscale(xscale)
    ax.set_yscale(yscale)
    ax.set_xlabel(xlabel, labelpad=0.0)
    ax.set_ylabel(ylabel, labelpad=0.5)
    ax.set_xlim(xlim_min, xlim_max)
    ax.set_ylim(ylim_min, ylim_max)

    # ax.tick_params(axis="y", which="major", pad=0.5)
    # ax.tick_params(axis="y", which="minor", pad=-1.0)
    # ax.tick_params(axis="x", which="major", pad=0.5)
    isnothing(xticks) || ax.set_xticks(xticks)
    isnothing(yticks) || ax.set_yticks(yticks)
    plt.setp(ax.get_xminorticklabels(), visible=false)
    ax.legend(; frameon=false, 
        loc=legend_loc, bbox_to_anchor,
        handlelength=legend_handlelength, handletextpad=legend_handletextpad, labelspacing=legend_labelspacing, borderpad=legend_borderpad)
    # plt.tight_layout()
    plt.subplots_adjust(; left=subplot_left, right=subplot_right, top=subplot_top, bottom=subplot_bottom)
    # plt.show()
    return ax
end

function plot_ler!(ax, xs_lines::Vector{<:Vector{<:Real}}, ys_lines::Vector{<:Vector{<:Real}},
        label_lines::Vector{<:Union{Nothing, String}};

        # line styles
        markers = DEFAULT_MARKERS,
        markerfacecolors = DEFAULT_MARKERFACECOLORS,
        markeredgecolors = DEFAULT_MARKEREDGECOLORS,
        colors = DEFAULT_COLORS,
        alphas = ones(length(xs_lines)),

        # x and y axis
        xlabel::String = "Code distance", ylabel::String = "Logical error rate",
        xscale::String = "linear", yscale::String = "log",
        xlim_min = nothing, xlim_max = nothing, ylim_min = nothing, ylim_max = nothing,

        # legend settings
        legend_loc = "lower right")
    num_lines = length(xs_lines)
    @assert num_lines == length(ys_lines) == length(label_lines)

    for (i, (xs, ys, label)) in enumerate(zip(xs_lines, ys_lines, label_lines))
        marker = markers[(i-1) % length(markers) + 1]
        markerfacecolor = markerfacecolors[(i-1) % length(markerfacecolors) + 1]
        markeredgecolor = markeredgecolors[(i-1) % length(markeredgecolors) + 1]
        color = colors[(i-1) % length(colors) + 1]
        alpha = alphas[(i-1) % length(alphas) + 1]
        ax.plot(xs, ys;
            label, 
            marker, 
            # markerfacecolor, markeredgecolor, 
            color, alpha,
            linewidth=.75, markersize=4.5, markeredgewidth=.75)
    end

    ax.set_xscale(xscale)
    ax.set_yscale(yscale)
    ax.set_xlabel(xlabel, labelpad=0.0)
    ax.set_ylabel(ylabel, labelpad=0.5)
    ax.set_xlim(xlim_min, xlim_max)
    ax.set_ylim(ylim_min, ylim_max)

    # ax.tick_params(axis="y", which="major", pad=0.5)
    # ax.tick_params(axis="y", which="minor", pad=-1.0)
    # ax.tick_params(axis="x", which="major", pad=0.5)
    # ax.set_xticks(sort(collect(unique_xs)))
    plt.setp(ax.get_xminorticklabels(), visible=false)
    ax.legend(frameon=false, loc=legend_loc, 
        handlelength=1., handletextpad=0.5, labelspacing=0.5, borderpad=.1)
    # plt.tight_layout()
    plt.subplots_adjust(left=0.2, right=0.95, top=0.95, bottom=0.1)
    # plt.show()
    return ax
end

function plot_groups_with_error_bar!(ax, grouped_lines::Dict{CK, Dict{RK, ResultLine}};
        # x and y axis
        xlabel::String = "Code distance", ylabel::String = "Logical error rate",
        xscale::String = "linear", yscale::String = "log",
        xlim_min = nothing, xlim_max = nothing, ylim_min = nothing, ylim_max = nothing,
        xticks = nothing, yticks = nothing,

        # group labels
        column_labels::Dict{CK, String}, row_labels::Dict{RK, String}, row_title::String = "",

        # style maps
        marker_map::Function = (rk, ck) -> "o", 
        color_map::Function = (rk, ck) -> "orange", 
        alpha_map::Function = (rk, ck) -> 1.0,
        markerfacecolor_map::Function = color_map,
        markeredgecolor_map::Function = color_map,

        # line styles
        linewidth=nothing, markersize=nothing, markeredgewidth=nothing,
        errorbar_capsize=nothing,

        # legend settings
        legend_frameon=false, 
        legend_loc = "lower right", bbox_to_anchor=nothing,
        legend_handletextpad = nothing,
        legend_handlelength = nothing, 
        legend_columnspacing = nothing,
        legend_labelspacing = nothing,
        legend_borderpad = nothing,

        # subplot settings
        subplot_left=nothing, subplot_right=nothing, 
        subplot_top=nothing, subplot_bottom=nothing,

        # other settings
        rev_row_keys::Bool = false
        ) where {CK, RK}
    
    m_patches = matplotlib.patches

    column_keys = unique(keys(column_labels))
    row_keys = sort(unique(keys(row_labels)); rev = rev_row_keys)

    patches_columns = [[m_patches.Patch(color="none", label=column_labels[ck])] for ck in column_keys]
    pushfirst!(patches_columns, [m_patches.Patch(color="none", label=row_title)])

    for (c_i, ck) in enumerate(column_keys)
        ck_lines = grouped_lines[ck]
        for (r_i, rk) in enumerate(row_keys)
            if c_i == 1
                push!(patches_columns[1], m_patches.Patch(color="none", label=row_labels[rk]))
            end
            line = ck_lines[rk]
            xs = line.xs
            ys = line.ys
            yerr = line.yerrs
            label = "\0"
            marker = marker_map(rk, ck)
            color = color_map(rk, ck)
            markeredgecolor = markeredgecolor_map(rk, ck)
            markerfacecolor = markerfacecolor_map(rk, ck)
            alpha = alpha_map(rk, ck)
            
            # l, = ax.plot([], [];
            #     label, marker, color, alpha,
            #     markeredgecolor, markerfacecolor,
            #     linewidth, markersize, markeredgewidth)
            l = ax.errorbar(xs, ys; 
                yerr, marker, color, alpha,
                markeredgecolor, markerfacecolor,
                linewidth, markersize, markeredgewidth,
                capsize=errorbar_capsize)
            push!(patches_columns[c_i+1], l)
        end
    end
    @assert all(length(p_cls) == length(row_keys) + 1 for p_cls in patches_columns)
    patches = reduce(vcat, patches_columns)
    @assert patches isa Vector
    lg = ax.legend(;
        ncol=length(column_keys)+1, handles=patches,
        frameon=legend_frameon, 
        loc=legend_loc, bbox_to_anchor,
        handletextpad=legend_handletextpad, 
        handlelength=legend_handlelength, columnspacing=legend_columnspacing,
        labelspacing=legend_labelspacing, borderpad=legend_borderpad
    )

    for (i, text) in enumerate(lg.get_texts())
        nrows = length(row_keys) + 1
        r_i = (i - 1) % nrows + 1
        c_i = (i - 1) ÷ nrows + 1
        if (r_i == 1) || (c_i == 1)
            text.set_color("black")
        else
            text.set_color("none")
        end
    end

    ax.set_xscale(xscale)
    ax.set_yscale(yscale)
    ax.set_xlabel(xlabel, labelpad=0.0)
    ax.set_ylabel(ylabel, labelpad=0.5)
    ax.set_ylim(xlim_min, xlim_max)
    ax.set_ylim(ylim_min, ylim_max)

    # ax.tick_params(axis="y", which="major", pad=0.5)
    # ax.tick_params(axis="y", which="minor", pad=-1.0)
    # ax.tick_params(axis="x", which="major", pad=0.5)
    isnothing(xticks) || ax.set_xticks(xticks)
    isnothing(yticks) || ax.set_yticks(yticks)
    plt.setp(ax.get_xminorticklabels(), visible=false)
    # plt.tight_layout()
    plt.subplots_adjust(left=subplot_left, right=subplot_right, top=subplot_top, bottom=subplot_bottom)
    return ax
end
